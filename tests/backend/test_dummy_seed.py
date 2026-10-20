from collections import Counter
from datetime import date, timedelta

import pytest
from tests.backend.test_sales_analysis import MemoryStore

from eclado_backend.services.dashboard_service import DashboardService
from eclado_backend.services.dummy_seed_service import build_dummy_dataset
from eclado_backend.services.marketing_preview import RulePreviewAdvisor
from eclado_backend.services.sales_import_service import SalesImportService
from eclado_backend.services.sales_service import SalesAnalysisService, age_band
from eclado_backend.stores.catalog_store import CatalogSnapshotStore
from eclado_backend.stores.dashboard_store import DemoDashboardStore
from eclado_shared.schemas.sales import DummySalesDataset


def seeded_data() -> tuple[DummySalesDataset, dict[str, str]]:
    catalog = DashboardService(
        DemoDashboardStore(), RulePreviewAdvisor(), CatalogSnapshotStore()
    ).get_dashboard(date(2026, 10, 1), date(2026, 10, 20), "pending").catalog
    return build_dummy_dataset(catalog), {row.product_id: row.name for row in catalog}


def test_seed_variety_and_reconciliation() -> None:
    data, names = seeded_data()
    store = MemoryStore()
    importer = SalesImportService(store, set(names))
    assert importer.import_dataset(data).reviews == 400
    assert importer.import_dataset(data).status == "unchanged"
    assert len(data.customers) == len(data.orders) == 2000
    customers = {row.customer_id: row for row in data.customers}
    assert Counter(row.gender for row in data.customers) == {"male": 1000, "female": 1000}
    assert len({row.region for row in data.customers}) == 25
    assert len({row.customer_id for row in data.reviews}) == 400
    assert sum(row.rating >= 4 for row in data.reviews) == 200
    assert sum(row.rating <= 2 for row in data.reviews) == 200
    assert {age_band(customers[o.customer_id].birth_year, o.paid_on.year) for o in data.orders} == {
        f"{age}대" for age in range(10, 90, 10)
    }
    assert {len(order.items) for order in data.orders} == {1, 2, 3, 4, 5}
    assert len({item.product_id for order in data.orders for item in order.items}) == len(names)
    assert any(item.ean and item.capacity for order in data.orders for item in order.items)
    assert len(data.refunds) == 200
    result = SalesAnalysisService(names).analyze(
        data, "dummy", data.coverage_start, data.coverage_end
    )
    expected = sum(
        item.quantity * item.unit_price - item.discount
        for order in data.orders for item in order.items
    ) - sum(row.amount for row in data.refunds)
    assert result.totals and result.totals.net == expected
    assert result.totals.orders == 2000 and result.totals.buyers == 1600
    assert result.repeat_buyers == 400
    assert result.review_count == result.reviewer_count == 400
    assert sum(row.net or 0 for row in result.region_cohorts) == expected
    assert sum(row.net or 0 for row in result.gender_cohorts) == expected
    assert sum(row.net or 0 for row in result.age_cohorts) == expected
    assert sum(row.net or 0 for row in result.daily) == expected
    assert sum(row.net or 0 for row in result.monthly) == expected
    assert sum(row.net for row in result.products) == expected
    assert result.daily[-1].ma365 is not None


def test_bad_review_cannot_replace_persisted_data() -> None:
    data, names = seeded_data()
    memory = MemoryStore()
    importer = SalesImportService(memory, set(names))
    importer.import_dataset(data)
    broken = data.model_copy(deep=True)
    broken.reviews[0].customer_id = "dummy-nonbuyer"
    with pytest.raises(ValueError):
        importer.import_dataset(broken)
    assert memory.data == data
    broken = data.model_copy(deep=True)
    broken.reviews[0].created_on = data.coverage_end + timedelta(days=1)
    with pytest.raises(ValueError):
        importer.import_dataset(broken)
    broken = data.model_copy(deep=True)
    broken.reviews.append(broken.reviews[0].model_copy(update={"review_id": "dummy-duplicate"}))
    with pytest.raises(ValueError):
        importer.import_dataset(broken)


def test_reviews_respect_period_and_customer_filters() -> None:
    data, names = seeded_data()
    service = SalesAnalysisService(names)
    all_rows = service.analyze(data, "dummy", data.coverage_start, data.coverage_end)
    female = service.analyze(data, "dummy", data.coverage_start, data.coverage_end, gender="female")
    male = service.analyze(data, "dummy", data.coverage_start, data.coverage_end, gender="male")
    assert female.review_count + male.review_count == all_rows.review_count
    day = data.coverage_end
    one_day = service.analyze(data, "dummy", day, day)
    assert one_day.review_count == sum(row.created_on == day for row in data.reviews)
