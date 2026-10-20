from datetime import UTC, datetime

from eclado_backend.services.public_catalog import (
    ORIGIN,
    category_id,
    collect_public_catalog,
    parse_catalog_page,
)
from eclado_backend.stores.catalog_store import CatalogSnapshotStore

HTML = """<p class="prdCount">전체 <strong>1</strong>개</p>
<li id="anchorBoxId_67"><a name="anchorBoxName_67" href="/product/test/67/">
<img id="eListPrdImage67_1" src="/product.jpg" alt="공식 상품명"></a>
<ul><li column_name="product_price">판매가 <span>55,000원</span></li>
<li column_name="prd_price_sale">할인판매가 <span>30,250원</span></li>
<li column_name="price_custom">소비자가 <span>70,000원</span></li></ul></li>"""


def test_parser_keeps_three_prices_and_source_without_guessing() -> None:
    observed = datetime(2026, 10, 20, tzinfo=UTC)
    rows, _, _ = parse_catalog_page(HTML, f"{ORIGIN}/product/list.html?cate_no=43", observed)
    assert len(rows) == 1
    assert rows[0].product_id == "67"
    assert rows[0].name == "공식 상품명"
    price = rows[0].observations[0]
    assert (price.sale_price, price.discounted_price, price.list_price) == (55000, 30250, 70000)
    assert price.observed_at == observed
    missing = HTML.replace("55,000원", "별도 문의")
    rows, _, _ = parse_catalog_page(missing, ORIGIN, observed)
    assert rows[0].observations[0].sale_price is None


def test_collection_deduplicates_products_and_checks_declared_counts() -> None:
    class FakeClient:
        def get_text(self, url: str) -> str:
            assert url.startswith(ORIGIN)
            assert "/api" not in url and "/member" not in url
            return HTML

    result = collect_public_catalog(FakeClient())
    assert result.complete
    assert len(result.visited_urls) == 5
    assert len(result.products) == 1
    assert len(result.products[0].observations) == 5
    assert result.declared_counts["43"] == result.collected_counts["43"] == 1


def test_collection_marks_missing_products_incomplete() -> None:
    class IncompleteClient:
        def get_text(self, url: str) -> str:
            return HTML.replace("<strong>1</strong>", "<strong>2</strong>")

    assert not collect_public_catalog(IncompleteClient()).complete
    assert category_id("https://other.example/product/list.html?cate_no=43") is None


def test_shipped_snapshot_has_real_names_prices_and_full_primary_category() -> None:
    snapshot = CatalogSnapshotStore().load()
    assert snapshot.complete
    assert snapshot.declared_counts["43"] == snapshot.collected_counts["43"]
    assert len({row.product_id for row in snapshot.products}) == len(snapshot.products)
    assert all("데모" not in row.name for row in snapshot.products)
    assert all(row.observations and row.url.startswith(ORIGIN) for row in snapshot.products)
    assert all(row.observations[0].sale_price is not None for row in snapshot.products)
