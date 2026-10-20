from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from eclado_backend.api.routers.sales_router import get_dummy_store
from eclado_backend.main import app
from eclado_backend.services.sales_import_service import SalesImportService
from eclado_backend.services.sales_service import SalesAnalysisService
from eclado_backend.stores.sales_store import LocalDummySalesStore
from eclado_shared.schemas.sales import (
    DummyCustomer,
    DummyItem,
    DummyOrder,
    DummyRefund,
    DummySalesDataset,
)


class MemoryStore:
    def __init__(self) -> None:
        self.data: DummySalesDataset | None = None

    def load(self) -> DummySalesDataset | None:
        return self.data

    def save(self, dataset: DummySalesDataset) -> tuple[bool, str]:
        changed = dataset != self.data
        self.data = dataset.model_copy(deep=True)
        return changed, "fake-hash"


def thousand_records() -> DummySalesDataset:
    start = date(2020, 1, 1)
    return DummySalesDataset(
        schema_version="1",
        synthetic=True,
        coverage_start=start,
        coverage_end=start + timedelta(days=999),
        customers=[
            DummyCustomer(
                customer_id=f"dummy-c-{i}",
                gender="female" if i % 2 else "male",
                birth_year=1940 + i % 70,
            )
            for i in range(1000)
        ],
        orders=[
            DummyOrder(
                order_id=f"dummy-o-{i}",
                customer_id=f"dummy-c-{i}",
                paid_on=start + timedelta(days=i),
                shipping=3000,
                items=[
                    DummyItem(
                        item_id=f"dummy-i-{i}",
                        product_id="11" if i % 2 else "12",
                        quantity=2,
                        unit_price=20000,
                        discount=4000,
                    )
                ],
            )
            for i in range(1000)
        ],
    )


def test_thousand_customers_and_orders_reconcile_in_all_views() -> None:
    data = thousand_records()
    memory = MemoryStore()
    importer = SalesImportService(memory, {"11", "12"})
    assert importer.import_dataset(data).orders == 1000
    assert importer.import_dataset(data).status == "unchanged"
    assert memory.data is not None
    result = SalesAnalysisService({"11": "상품 A", "12": "상품 B"}).analyze(
        memory.data, "dummy", data.coverage_start, data.coverage_end
    )
    assert result.complete and result.totals is not None
    assert result.totals.orders == result.totals.buyers == 1000
    assert result.totals.net == 36000000
    assert sum(row.net or 0 for row in result.daily) == result.totals.net
    assert sum(row.net or 0 for row in result.monthly) == result.totals.net
    assert sum(row.net or 0 for row in result.yearly) == result.totals.net
    assert sum(row.net for row in result.products) == result.totals.net
    assert sum(row.count for row in result.order_amounts) == 1000
    assert sum(row.count for row in result.customer_averages) == 1000
    assert result.daily[18].ma20 is None and result.daily[19].ma20 == 36000
    assert result.daily[28].ma30 is None and result.daily[29].ma30 == 36000
    assert result.daily[363].ma365 is None and result.daily[364].ma365 == 36000
    assert any(row.label == "80대" for row in result.age_cohorts)
    assert result.gender_trends and result.cohort_trends


def test_averages_use_history_before_selected_start_and_missing_is_not_zero() -> None:
    data = thousand_records()
    service = SalesAnalysisService({"11": "A", "12": "B"})
    cropped = service.analyze(data, "dummy", date(2021, 1, 1), date(2021, 1, 2))
    assert cropped.daily[0].ma365 == 36000
    missing = service.analyze(data, "dummy", date(2019, 12, 31), date(2020, 1, 2))
    assert missing.daily[0].net is None
    assert not missing.complete
    pending = service.analyze(None, "pending", date(2020, 1, 1), date(2026, 10, 20))
    assert pending.totals is None and pending.daily == []


def test_refund_is_counted_once_on_completion_and_in_original_purchase_age_band() -> None:
    data = thousand_records()
    data.refunds = [
        DummyRefund(
            refund_id="dummy-r-1",
            order_id="dummy-o-0",
            item_id="dummy-i-0",
            completed_on=date(2021, 1, 1),
            amount=10000,
            quantity=1,
        )
    ]
    service = SalesAnalysisService({"11": "A", "12": "B"})
    before = service.analyze(data, "dummy", date(2020, 1, 1), date(2020, 1, 1))
    after = service.analyze(data, "dummy", date(2021, 1, 1), date(2021, 1, 1))
    assert before.totals and before.totals.net == 36000
    assert after.totals and after.totals.net == 26000
    SalesImportService(MemoryStore(), {"11", "12"}).validate(data)


def test_invalid_import_does_not_replace_prior_dataset() -> None:
    memory = MemoryStore()
    data = thousand_records()
    importer = SalesImportService(memory, {"11", "12"})
    importer.import_dataset(data)
    broken = data.model_copy(deep=True)
    broken.orders[0].items[0].product_id = "999999"
    with pytest.raises(ValueError):
        importer.import_dataset(broken)
    assert memory.data == data
    broken = data.model_copy(deep=True)
    broken.orders[0].items[0].discount = 999999
    with pytest.raises(ValueError):
        importer.import_dataset(broken)
    broken = data.model_copy(deep=True)
    broken.customers.append(broken.customers[0])
    with pytest.raises(ValueError):
        importer.import_dataset(broken)


def test_gender_age_and_behavior_filters_and_small_group_suppression() -> None:
    data = thousand_records()
    service = SalesAnalysisService({"11": "A", "12": "B"})
    female = service.analyze(data, "dummy", data.coverage_start, data.coverage_end, gender="female")
    assert female.totals and female.totals.buyers == 500
    repeat = service.analyze(
        data, "dummy", data.coverage_start, data.coverage_end, persona="repeat"
    )
    assert repeat.totals is None
    assert all(row.net is None for row in repeat.daily)
    discount = service.analyze(
        data, "dummy", data.coverage_start, data.coverage_end, persona="discount"
    )
    assert discount.totals and discount.totals.orders == 1000
    young = service.analyze(data, "dummy", data.coverage_start, data.coverage_end, age="10대")
    assert young.totals and 0 < young.totals.buyers < 1000


def test_alert_top_five_each_direction_and_zero_baseline() -> None:
    data = thousand_records()
    data.orders = []
    data.coverage_start, data.coverage_end = date(2020, 1, 1), date(2020, 3, 1)
    names = {str(key): f"상품 {key}" for key in range(11, 25)}
    for index, product in enumerate(names):
        for day, amount in [
            (date(2020, 2, 29), 10000 if index < 7 else 400000),
            (date(2020, 3, 1), 400000 if index < 7 else 10000),
        ]:
            key = f"dummy-{product}-{day}"
            data.orders.append(
                DummyOrder(
                    order_id=key,
                    customer_id="dummy-c-0",
                    paid_on=day,
                    items=[
                        DummyItem(item_id=key, product_id=product, quantity=1, unit_price=amount)
                    ],
                )
            )
    result = SalesAnalysisService(names).analyze(
        data, "dummy", data.coverage_start, data.coverage_end
    )
    assert len([row for row in result.alerts if row.window == 1 and row.direction == "up"]) == 5
    assert len([row for row in result.alerts if row.window == 1 and row.direction == "down"]) == 5
    assert all(len(row.series) == row.window * 2 for row in result.alerts)
    data.orders = [order for order in data.orders if order.paid_on == data.coverage_end]
    result = SalesAnalysisService(names).analyze(
        data, "dummy", data.coverage_start, data.coverage_end
    )
    assert result.alerts and all(row.percent is None for row in result.alerts)


def test_api_thousand_record_import_and_validation_use_isolated_fake_store() -> None:
    memory = MemoryStore()
    app.dependency_overrides[get_dummy_store] = lambda: memory
    try:
        client = TestClient(app)
        data = thousand_records()
        assert (
            client.post("/api/v1/sales/dummy", json=data.model_dump(mode="json")).status_code == 200
        )
        assert (
            client.post("/api/v1/sales/dummy", json=data.model_dump(mode="json")).json()["status"]
            == "unchanged"
        )
        response = client.get("/api/v1/sales/preview?source=dummy&start=2020-01-01&end=2022-09-26")
        assert response.status_code == 200
        assert response.json()["totals"]["orders"] == 1000
        assert client.get("/api/v1/sales/preview?age=bad").status_code == 422
        assert client.get("/api/v1/sales/preview?start=2019-01-01").status_code == 422
        assert client.get("/api/v1/sales/preview?source=live").status_code == 422
        payload = data.model_dump(mode="json")
        payload["phone"] = "not-allowed"
        assert client.post("/api/v1/sales/dummy", json=payload).status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_local_dummy_store_survives_reload_without_duplicate_sales() -> None:
    path = Path.cwd() / ".cache" / f"test-sales-{uuid4().hex}.json"
    try:
        store = LocalDummySalesStore(path)
        data = thousand_records()
        result = SalesImportService(store, {"11", "12"}).import_dataset(data)
        assert result.status == "imported"
        reloaded = LocalDummySalesStore(path)
        assert reloaded.load() == data
        assert SalesImportService(reloaded, {"11", "12"}).import_dataset(data).status == "unchanged"
    finally:
        path.unlink(missing_ok=True)
