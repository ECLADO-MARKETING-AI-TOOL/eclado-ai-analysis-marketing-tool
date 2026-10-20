import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest
from tests.preview_session_fakes import MemoryPreviewSessionStore

from eclado_admin.repositories.dashboard_repository import DashboardRepository
from eclado_admin.repositories.sales_repository import SalesRepository
from eclado_backend.services.dashboard_service import DashboardService
from eclado_backend.services.marketing_preview import RulePreviewAdvisor
from eclado_backend.services.preview_session_service import PreviewSessionService as DemoSessions
from eclado_backend.stores.catalog_store import CatalogSnapshotStore
from eclado_backend.stores.dashboard_store import DemoDashboardStore
from eclado_shared.schemas.sales import SalesAnalysis

APP = Path("admin/eclado_admin/main.py").resolve()


def test_session_absolute_expiry_revocation_and_unknown_tokens() -> None:
    sessions = DemoSessions(MemoryPreviewSessionStore())
    with patch("eclado_backend.services.preview_session_service.time", return_value=1000):
        first, expires = sessions.issue()
        second, _ = sessions.issue()
        assert first != second and expires == 4600
        assert sessions.expires_at("forged" * 8) is None
        assert sessions.expires_at({"user": "user@example.com"}) is None
    with patch("eclado_backend.services.preview_session_service.time", return_value=4599):
        assert sessions.expires_at(first) == expires
        assert sessions.expires_at(first) == expires  # Reading does not slide the deadline.
        sessions.revoke(second)
        assert sessions.expires_at(second) is None
        assert sessions.expires_at(first) == expires
    with patch("eclado_backend.services.preview_session_service.time", return_value=4600):
        assert sessions.expires_at(first) is None


def test_refresh_restores_then_expiry_and_logout_prevent_restore() -> None:
    sessions = DemoSessions(MemoryPreviewSessionStore())
    service = DashboardService(DemoDashboardStore(), RulePreviewAdvisor(), CatalogSnapshotStore())
    with (
        patch("eclado_admin.demo_auth.demo_sessions", return_value=sessions),
        patch("eclado_admin.demo_auth.browser_session", return_value=None) as browser,
        patch("eclado_backend.services.preview_session_service.time", return_value=1000) as clock,
        patch.object(DashboardRepository, "get_dashboard") as api,
        patch.object(
            SalesRepository,
            "analyze",
            side_effect=lambda source, start, end, *args: SalesAnalysis(
                source=source, start=start, end=end, status="pending"
            ),
        ),
    ):
        # Repository method uses source,start,end, while the service uses start,end,source.
        api.side_effect = lambda source, start, end: service.get_dashboard(start, end, source)
        first = AppTest.from_file(APP).run(timeout=30)
        first.session_state["sales_page"] = "매출·상품·리뷰 AI"
        first.text_input[0].set_value("user@example.com")
        first.text_input[1].set_value("x")
        first.button[0].click().run(timeout=30)
        token = first.session_state["demo_session_token"]
        assert not first.exception and first.radio(key="sales_page").value == "매출·상품·리뷰 AI"
        browser.return_value = token
        clock.return_value = 4599
        refreshed = AppTest.from_file(APP)
        refreshed.session_state["sales_page"] = "매출·상품·리뷰 AI"
        refreshed.run(timeout=30)
        assert (
            not refreshed.exception
            and refreshed.radio(key="sales_page").value == "매출·상품·리뷰 AI"
        )
        assert refreshed.session_state["eclado_demo_user"] == "user@example.com"
        refreshed.button(key="demo_logout").click().run(timeout=30)
        assert not refreshed.tabs and len(refreshed.text_input) == 2
        assert sessions.expires_at(token) is None
        api.reset_mock()
        AppTest.from_file(APP).run(timeout=30)
        api.assert_not_called()  # Stale browser tokens cannot undo logout.
        clock.return_value = 1000
        expiring, _ = sessions.issue()
        browser.return_value = expiring
        clock.return_value = 4600
        expired = AppTest.from_file(APP).run(timeout=30)
        assert len(expired.text_input) == 2 and not expired.exception
        api.assert_not_called()


def test_browser_storage_refresh_expiry_and_clear() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is optional; needed only to execute the browser bridge harness")
    result = subprocess.run(
        [node, "tests/admin/demo_session_harness.mjs"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
