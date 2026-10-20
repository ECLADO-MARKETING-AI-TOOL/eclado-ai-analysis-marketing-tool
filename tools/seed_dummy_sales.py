"""Seed the local running API through repositories; keep synthetic data persisted."""

from datetime import date

from eclado_admin.repositories.dashboard_repository import DashboardRepository
from eclado_admin.repositories.sales_repository import SalesRepository
from eclado_backend.services.dummy_seed_service import build_dummy_dataset


def main() -> None:
    catalog = DashboardRepository().get_dashboard("pending", date(2026, 10, 1), date(2026, 10, 20))
    dataset = build_dummy_dataset(catalog.catalog)
    repository = SalesRepository()
    imported = repository.import_dummy(dataset)
    result = repository.analyze("dummy", dataset.coverage_start, dataset.coverage_end)
    expected = sum(
        item.quantity * item.unit_price - item.discount
        for order in dataset.orders for item in order.items
    ) - sum(row.amount for row in dataset.refunds)
    assert result.totals is not None and result.totals.net == expected
    assert result.totals.orders == 2000 and result.review_count == 400
    assert sum(row.net or 0 for row in result.daily) == expected
    assert sum(row.net or 0 for row in result.monthly) == expected
    assert sum(row.net for row in result.products) == expected
    assert repository.import_dummy(dataset).status == "unchanged"
    print(imported.model_dump_json())
    print(result.totals.model_dump_json())
    print(f"products={len(result.products)} regions={len(result.region_cohorts)} "
          f"reviews={result.review_count} reviewers={result.reviewer_count}")


if __name__ == "__main__":
    main()
