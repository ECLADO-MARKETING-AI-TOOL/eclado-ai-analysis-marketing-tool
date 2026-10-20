"""One-shot, public catalog collection; never fetches customers or orders."""

import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from eclado_backend.schemas.catalog_schema import (
    CatalogProduct,
    CatalogSnapshot,
    PriceObservation,
)

ORIGIN = "https://ecladomall.co.kr"
USER_AGENT = "EcladoCatalogPreview/0.1"


@dataclass
class Node:
    tag: str
    attrs: dict[str, str]
    children: list["Node | str"] = field(default_factory=list)

    def walk(self) -> list["Node"]:
        return [self] + [
            descendant
            for child in self.children
            if isinstance(child, Node)
            for descendant in child.walk()
        ]

    def text(self) -> str:
        return " ".join(
            child.text() if isinstance(child, Node) else child for child in self.children
        )


class CatalogHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, {key: value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if self.stack[-1].tag not in {"script", "style"}:
            self.stack[-1].children.append(data)


def category_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc != "ecladomall.co.kr":
        return None
    if parsed.path == "/product/list.html":
        value = parse_qs(parsed.query).get("cate_no", [""])[0]
        return value if value.isdigit() else None
    match = re.fullmatch(r"/category/[^/]+/(\d+)/?", parsed.path)
    return match[1] if match else None


def parse_catalog_page(
    html: str, url: str, observed_at: datetime
) -> tuple[list[CatalogProduct], dict[str, str], int]:
    parser = CatalogHtmlParser()
    parser.feed(html)
    nodes = parser.root.walk()
    products: list[CatalogProduct] = []
    categories: dict[str, str] = {}
    last_page = 1
    for node in nodes:
        if node.tag == "a":
            href = urljoin(url, node.attrs.get("href", ""))
            category = category_id(href)
            if category:
                label = re.sub(r"\s*\([^)]*\)\s*$", "", node.text()).strip()
                if label and not label.isdigit() and "페이지" not in label:
                    categories[category] = label
                if category == category_id(url):
                    page = parse_qs(urlparse(href).query).get("page", ["1"])[0]
                    if page.isdigit():
                        last_page = max(last_page, int(page))
        marker = re.fullmatch(r"anchorBoxId_(\d+)", node.attrs.get("id", ""))
        if not marker:
            continue
        descendants = node.walk()
        image = next(
            (
                item
                for item in descendants
                if item.tag == "img" and item.attrs.get("id", "").startswith("eListPrdImage")
            ),
            None,
        )
        anchor = next(
            (
                item
                for item in descendants
                if item.tag == "a" and item.attrs.get("name") == f"anchorBoxName_{marker[1]}"
            ),
            None,
        )
        if image is None or anchor is None or not image.attrs.get("alt"):
            raise ValueError(f"Product {marker[1]} has no unambiguous name/link")
        amounts: dict[str, int | None] = {}
        for item in descendants:
            column = item.attrs.get("column_name")
            if column in {"product_price", "prd_price_sale", "price_custom"}:
                matches = re.findall(r"([\d,]+)\s*원", item.text())
                amounts[column] = int(matches[0].replace(",", "")) if len(matches) == 1 else None
        products.append(
            CatalogProduct(
                product_id=marker[1],
                name=image.attrs["alt"].strip(),
                url=urljoin(url, anchor.attrs["href"]),
                image_url=urljoin(url, image.attrs.get("src", "")),
                observations=[
                    PriceObservation(
                        source_url=url,
                        observed_at=observed_at,
                        sale_price=amounts.get("product_price"),
                        discounted_price=amounts.get("prd_price_sale"),
                        list_price=amounts.get("price_custom"),
                    )
                ],
            )
        )
    return products, categories, last_page


class PublicPageClient(Protocol):
    def get_text(self, url: str) -> str: ...


class HttpPublicPageClient:
    def __init__(self) -> None:
        self._robots: RobotFileParser | None = None

    def get_text(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "ecladomall.co.kr":
            raise ValueError("Only the official public mall is allowed")
        if parsed.path not in {"/", "/robots.txt", "/product/list.html"}:
            raise ValueError("Only public catalog lists are allowed")
        if self._robots is None and parsed.path != "/robots.txt":
            robots = RobotFileParser()
            robots.parse(self.get_text(f"{ORIGIN}/robots.txt").splitlines())
            self._robots = robots
        if self._robots is not None and not self._robots.can_fetch(USER_AGENT, url):
            raise ValueError("robots.txt disallows this URL")
        time.sleep(1)
        # No cookies, login, internal APIs, scripts, redirects or anti-bot bypass.
        response = httpx.get(
            url,
            timeout=30,
            trust_env=False,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=False,
        )
        response.raise_for_status()
        if response.is_redirect:
            raise ValueError("Unexpected redirect; manual review required")
        if (
            "text/html" not in response.headers.get("content-type", "")
            and parsed.path != "/robots.txt"
        ):
            raise ValueError("Unexpected public page type")
        return response.text


def collect_public_catalog(client: PublicPageClient) -> CatalogSnapshot:
    snapshot = CatalogSnapshot(observed_at=datetime.now(UTC))
    queue = [
        f"{ORIGIN}/product/list.html?cate_no={category}&page=1" for category in (43, 44, 45, 46)
    ] + [f"{ORIGIN}/"]
    scheduled = set(queue)
    products: dict[str, CatalogProduct] = {}
    labels: dict[str, str] = {}
    memberships: dict[str, set[str]] = {}
    while queue:
        url = queue.pop(0)
        if len(snapshot.visited_urls) >= 300:
            snapshot.errors.append("Public catalog page limit reached; coverage incomplete")
            break
        try:
            html = client.get_text(url)
            rows, categories, last_page = parse_catalog_page(html, url, datetime.now(UTC))
            if not rows and category_id(url) == "43":
                raise ValueError("Expected public product list is empty")
            snapshot.visited_urls.append(url)
            labels.update(categories)
            category = category_id(url)
            if category:
                memberships.setdefault(category, set()).update(row.product_id for row in rows)
                declared = re.search(
                    r'<p[^>]*class="prdCount"[^>]*>.*?<strong[^>]*>([\d,]+)</strong>',
                    html,
                    re.DOTALL,
                )
                if declared:
                    snapshot.declared_counts[category] = int(declared[1].replace(",", ""))
            for row in rows:
                if row.product_id in products:
                    existing = products[row.product_id]
                    if row.name != existing.name:
                        snapshot.errors.append(f"Name conflict for product {row.product_id}")
                    existing.observations.extend(row.observations)
                else:
                    products[row.product_id] = row
            links = [(key, 1) for key in categories]
            if category:
                links += [(category, page) for page in range(2, last_page + 1)]
            for key, page in links:
                link = f"{ORIGIN}/product/list.html?cate_no={key}&page={page}"
                if link not in scheduled:
                    scheduled.add(link)
                    queue.append(link)
        except (httpx.HTTPError, ValueError) as error:
            # Store URL and error type, never raw HTML containing scripts/identifiers.
            snapshot.errors.append(f"{url}: {type(error).__name__}")
        print(
            f"pages={len(snapshot.visited_urls)} products={len(products)} "
            f"remaining={len(queue)} errors={len(snapshot.errors)}",
            flush=True,
        )
    for product_id, product in products.items():
        product.categories = sorted(
            {
                labels.get(category, category)
                for category, members in memberships.items()
                if product_id in members
            }
        )
    snapshot.products = sorted(products.values(), key=lambda product: int(product.product_id))
    snapshot.collected_counts = {key: len(members) for key, members in memberships.items()}
    for key, expected in snapshot.declared_counts.items():
        if snapshot.collected_counts.get(key) != expected:
            snapshot.errors.append(f"Category {key}: declared count differs from collected count")
    snapshot.complete = not snapshot.errors and bool(snapshot.products)
    return snapshot
