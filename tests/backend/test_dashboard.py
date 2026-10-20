from datetime import date

from fastapi.testclient import TestClient

from eclado_backend.main import app
from eclado_backend.services.dashboard_service import DashboardService
from eclado_backend.services.marketing_preview import RulePreviewAdvisor
from eclado_backend.stores.dashboard_store import (
    DashboardDataset,
    DemoDashboardStore,
    OrderItem,
    Product,
    Refund,
)


class FakeStore:
    def load(self) -> DashboardDataset:
        return DashboardDataset(
            products=(Product("a", "가상 상품", "토너"), Product("b", "미판매 상품", "크림")),
            items=(OrderItem("order", "customer", "a", date(2026, 9, 30), 2, 50000, 10000, 3000),),
            refunds=(Refund("r1", "order", "a", date(2026, 10, 1), 1, 20000),),
            reviews=(),
        )


def test_refund_uses_completion_period_and_preserves_negative_sales() -> None:
    service = DashboardService(FakeStore(), RulePreviewAdvisor())
    september = service.get_dashboard(date(2026, 9, 30), date(2026, 9, 30), "demo")
    october = service.get_dashboard(date(2026, 10, 1), date(2026, 10, 1), "demo")
    assert september.totals is not None
    assert september.totals.net == 90000
    assert september.totals.shipping == 3000
    assert october.totals is not None
    assert october.totals.net == -20000
    assert october.totals.orders == 0
    assert october.products[0].units == -1
    assert october.products[1].units == 0
    assert october.products[1].average_rating is None


def test_pending_never_loads_demo_data_or_generates_recommendations() -> None:
    class UnavailableStore:
        def load(self) -> DashboardDataset:
            raise AssertionError("pending must not load a store")

    result = DashboardService(UnavailableStore(), RulePreviewAdvisor()).get_dashboard(
        date(2026, 10, 1), date(2026, 10, 20), "pending"
    )
    assert result.totals is None
    assert result.customers is None
    assert result.products == result.recommendations == []


def test_demo_aggregates_reconcile_across_days_products_and_orders() -> None:
    result = DashboardService(DemoDashboardStore(), RulePreviewAdvisor()).get_dashboard(
        date(2026, 10, 1), date(2026, 10, 20), "demo"
    )
    assert result.totals is not None
    assert result.customers is not None
    assert sum(day.net for day in result.daily) == result.totals.net
    assert sum(product.net for product in result.products) == result.totals.net
    assert (
        result.totals.gross - result.totals.discounts - result.totals.refunds == result.totals.net
    )
    assert (
        result.customers.first_time_buyers + result.customers.returning_buyers
        == result.totals.buyers
    )
    assert result.totals.other_revenue is None
    assert any(
        product.review_count == 0 and product.average_rating is None for product in result.products
    )
    assert result.recommendations


def test_preview_endpoint_rejects_invalid_source_dates_and_uncovered_period() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/dashboard/preview").status_code == 200
    for query in (
        "source=live",
        "start=2026-10-20&end=2026-10-01",
        "start=2025-01-01&end=2026-10-20",
        "source=demo&start=2026-09-01",
    ):
        assert client.get(f"/api/v1/dashboard/preview?{query}").status_code == 422
    response = client.get("/api/v1/dashboard/preview?source=pending")
    assert response.status_code == 200
    assert response.json()["totals"] is None
