"""Synthetic read store only. No customer data or external connections."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from eclado_backend.stores.catalog_store import CatalogSnapshotStore


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    category: str


@dataclass(frozen=True)
class OrderItem:
    order_id: str
    customer_id: str
    product_id: str
    paid_on: date
    quantity: int
    unit_price: int
    discount: int
    shipping: int


@dataclass(frozen=True)
class Refund:
    id: str
    order_id: str
    product_id: str
    completed_on: date
    quantity: int
    amount: int


@dataclass(frozen=True)
class Review:
    product_id: str
    created_on: date
    rating: int


@dataclass(frozen=True)
class DashboardDataset:
    products: tuple[Product, ...]
    items: tuple[OrderItem, ...]
    refunds: tuple[Refund, ...]
    reviews: tuple[Review, ...]


class DashboardStore(Protocol):
    def load(self) -> DashboardDataset: ...


DEMO_END = date(2026, 10, 20)


class DemoDashboardStore:
    def __init__(self, products: tuple[Product, ...] | None = None) -> None:
        self._products = products

    def load(self) -> DashboardDataset:
        products = self._products
        if products is None:
            catalog = CatalogSnapshotStore().load()
            products = tuple(
                Product(row.product_id, row.name, " / ".join(row.categories))
                for row in catalog.products
            )
        if len(products) < 6:
            raise ValueError("Preview scenario needs at least six catalog products")
        # Scenario amounts are synthetic and independent of public price observations.
        # Never use them for actual sales or a customer's historical purchase price.
        prices = (32000, 58000, 45000, 24000, 12000)
        items: list[OrderItem] = []
        refunds: list[Refund] = []
        reviews: list[Review] = []
        for offset in range(45):
            day = DEMO_END - timedelta(days=offset)
            for index in range(1 + offset % 4):
                product_index = (offset + index * 2) % 5
                order_id = f"DEMO-{offset:02d}-{index}"
                quantity = 1 + (offset + index) % 2
                price = prices[product_index]
                items.append(
                    OrderItem(
                        order_id,
                        f"demo-customer-{(offset + index) % 19:02d}",
                        products[product_index].id,
                        day,
                        quantity,
                        price,
                        price * quantity // 10,
                        3000,
                    )
                )
                if offset % 9 == 0 and index == 0:
                    refunds.append(
                        Refund(
                            f"refund-{order_id}",
                            order_id,
                            products[product_index].id,
                            day + timedelta(days=3),
                            1,
                            price * 9 // 10,
                        )
                    )
                if product_index < 4 and (offset + index) % 3 != 0:
                    reviews.append(
                        Review(products[product_index].id, day, (5, 4, 2, 4)[product_index])
                    )
        return DashboardDataset(products, tuple(items), tuple(refunds), tuple(reviews))
