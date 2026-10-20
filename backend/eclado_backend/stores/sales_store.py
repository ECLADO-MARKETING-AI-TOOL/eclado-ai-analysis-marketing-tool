"""Local synthetic datasets only. All persistence stays in stores."""

import hashlib
import os
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Protocol

from eclado_backend.stores.dashboard_store import DEMO_END, DemoDashboardStore
from eclado_shared.schemas.sales import (
    DummyCustomer,
    DummyItem,
    DummyOrder,
    DummyRefund,
    DummySalesDataset,
)

DUMMY_PATH = Path(__file__).resolve().parents[3] / ".local" / "sales_dummy.json"


class SalesStore(Protocol):
    def load(self) -> DummySalesDataset | None: ...
    def save(self, dataset: DummySalesDataset) -> tuple[bool, str]: ...


class LocalDummySalesStore:
    def __init__(self, path: Path = DUMMY_PATH) -> None:
        self._path = path

    def load(self) -> DummySalesDataset | None:
        if not self._path.exists():
            return None
        return DummySalesDataset.model_validate_json(self._path.read_text(encoding="utf-8"))

    def save(self, dataset: DummySalesDataset) -> tuple[bool, str]:
        serialized = dataset.model_dump_json()
        digest = hashlib.sha256(serialized.encode()).hexdigest()
        if self._path.exists() and self._path.read_text(encoding="utf-8") == serialized:
            return False, digest
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self._path.parent, suffix=".json", delete=False
        ) as output:
            temporary = Path(output.name)
            output.write(serialized)
        try:
            os.replace(temporary, self._path)
        finally:
            temporary.unlink(missing_ok=True)
        return True, digest


def demo_sales_dataset() -> DummySalesDataset:
    data = DemoDashboardStore().load()
    orders = [
        DummyOrder(
            order_id=f"dummy-{item.order_id}",
            customer_id=f"dummy-{item.customer_id}",
            paid_on=item.paid_on,
            shipping=item.shipping,
            items=[
                DummyItem(
                    item_id=f"dummy-item-{index}",
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    discount=item.discount,
                )
            ],
        )
        for index, item in enumerate(data.items)
    ]
    order_items = {order.order_id: order.items[0].item_id for order in orders}
    return DummySalesDataset(
        schema_version="1",
        synthetic=True,
        coverage_start=DEMO_END - timedelta(days=44),
        coverage_end=DEMO_END,
        customers=[
            DummyCustomer(customer_id=key)
            for key in sorted({order.customer_id for order in orders})
        ],
        orders=orders,
        refunds=[
            DummyRefund(
                refund_id=f"dummy-{refund.id}",
                order_id=f"dummy-{refund.order_id}",
                item_id=order_items[f"dummy-{refund.order_id}"],
                completed_on=refund.completed_on,
                quantity=refund.quantity,
                amount=refund.amount,
            )
            for refund in data.refunds
            if refund.completed_on <= DEMO_END
        ],
    )
