from datetime import date
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from eclado_admin.repositories.dashboard_repository import DashboardRepository
from eclado_admin.repositories.sales_repository import SalesRepository
from eclado_backend.services.dashboard_service import DashboardService
from eclado_backend.services.marketing_preview import RulePreviewAdvisor
from eclado_backend.stores.catalog_store import CatalogSnapshotStore
from eclado_backend.stores.dashboard_store import DemoDashboardStore
from eclado_shared.schemas.sales import SalesAnalysis

APP_PATH = Path("admin/eclado_admin/main.py").resolve()


@pytest.fixture(autouse=True)
def fake_sales() -> object:
    with patch.object(
        SalesRepository,
        "analyze",
        side_effect=lambda source, start, end, *args: SalesAnalysis(
            source=source, start=start, end=end, status="input pending"
        ),
    ):
        yield


def login_demo(screen: AppTest) -> AppTest:
    screen.session_state["sales_page"] = "매출·상품·리뷰 AI"
    screen.text_input[0].set_value("user@example.com")
    screen.text_input[1].set_value("any-preview-password")
    return screen.button[0].click().run(timeout=20)


def test_repository_passes_source_and_period_through_api() -> None:
    class FakeClient:
        def get(self, path: str) -> dict[str, object]:
            assert (
                path == "/api/v1/dashboard/preview?source=pending&start=2026-10-01&end=2026-10-20"
            )
            return {
                "source": "pending",
                "status": "대기",
                "start": "2026-10-01",
                "end": "2026-10-20",
                "metric_policy": "pending",
            }

    assert (
        DashboardRepository(FakeClient())
        .get_dashboard("pending", date(2026, 10, 1), date(2026, 10, 20))
        .totals
        is None
    )


def test_nested_navigation_catalog_prices_and_metadata_preserved() -> None:
    service = DashboardService(DemoDashboardStore(), RulePreviewAdvisor(), CatalogSnapshotStore())
    with patch.object(
        DashboardRepository,
        "get_dashboard",
        side_effect=lambda source, start, end: service.get_dashboard(start, end, source),
    ):
        screen = login_demo(AppTest.from_file(APP_PATH).run(timeout=20))
        assert not screen.exception and len(screen.radio) == 1
        assert screen.radio(key="sales_page").options == [
            "매출 요약",
            "매출 추이",
            "고객별 매출 추이",
            "매출·상품·리뷰 AI",
        ]
        catalog = screen.dataframe[0].value
        assert len(catalog) == 116 and "분류" not in catalog.columns
        memory = catalog[catalog["상품 ID"] == "67"].iloc[0]
        assert memory["용량"] == "30g / 50g / 200g"
        assert "30g: 8809820610091" in memory["EAN"]
        expected = {
            row.product_id: row.sale_price
            for row in service.get_dashboard(
                date(2026, 10, 1), date(2026, 10, 20), "pending"
            ).catalog
        }
        assert dict(zip(catalog["상품 ID"], catalog["판매가(원)"], strict=True)) == expected


def test_screen_catalog_backend_failure_shows_actionable_error() -> None:
    with patch.object(
        DashboardRepository, "get_dashboard", side_effect=httpx.ConnectError("offline")
    ):
        screen = login_demo(AppTest.from_file(APP_PATH).run(timeout=20))
    assert not screen.exception and screen.error


def test_logged_out_screen_never_requests_data() -> None:
    with patch.object(DashboardRepository, "get_dashboard") as request:
        screen = AppTest.from_file(APP_PATH).run(timeout=20)
    assert not screen.exception and len(screen.text_input) == 2
    request.assert_not_called()


def test_demo_login_validation_and_logout() -> None:
    service = DashboardService(DemoDashboardStore(), RulePreviewAdvisor(), CatalogSnapshotStore())
    with patch.object(
        DashboardRepository,
        "get_dashboard",
        side_effect=lambda source, start, end: service.get_dashboard(start, end, source),
    ) as request:
        screen = AppTest.from_file(APP_PATH).run(timeout=20)
        screen.text_input[0].set_value("someone@example.com")
        screen.text_input[1].set_value("anything")
        screen.button[0].click().run()
        assert screen.error
        request.assert_not_called()
        screen.text_input[0].set_value("user@example.com")
        screen.button[0].click().run()
        assert screen.error
        request.assert_not_called()
        login_demo(screen)
        assert not screen.exception and "demo_login_password" not in screen.session_state
        request.reset_mock()
        screen.button(key="demo_logout").click().run()
        assert len(screen.text_input) == 2 and "eclado_demo_user" not in screen.session_state
        request.assert_not_called()
