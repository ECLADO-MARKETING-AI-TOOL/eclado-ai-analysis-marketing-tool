from datetime import date
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from eclado_admin.repositories.sales_repository import SalesRepository
from eclado_backend.services.sales_service import SalesAnalysisService
from eclado_shared.schemas.sales import (
    DummyCustomer,
    DummyItem,
    DummyOrder,
    DummySalesDataset,
    Persona,
    SalesAnalysis,
    Source,
)


def test_three_sales_pages_render_with_a_thousand_dummy_customers_and_orders() -> None:
    data = DummySalesDataset(
        schema_version="1",
        synthetic=True,
        coverage_start=date(2020, 1, 1),
        coverage_end=date(2026, 10, 20),
        customers=[
            DummyCustomer(
                customer_id=f"dummy-c-{i}",
                gender="female" if i % 2 else "male",
                birth_year=1945 + i % 65,
            )
            for i in range(1000)
        ],
        orders=[
            DummyOrder(
                order_id=f"dummy-o-{i}",
                customer_id=f"dummy-c-{i}",
                paid_on=date(2026, 10, 1 + i % 20),
                items=[
                    DummyItem(
                        item_id=f"dummy-i-{i}",
                        product_id="11",
                        quantity=1,
                        unit_price=50000,
                        discount=5000,
                    )
                ],
            )
            for i in range(1000)
        ],
    )
    service = SalesAnalysisService({"11": "공식 상품 A"})

    def analyze(
        source: Source,
        start: date,
        end: date,
        gender: str,
        age: str,
        persona: Persona,
        alert_percent: float,
        min_change: int,
    ) -> SalesAnalysis:
        return service.analyze(
            data if source == "dummy" else None,
            source,
            start,
            end,
            gender,
            age,
            persona,
            alert_percent,
            min_change,
        )

    with patch.object(SalesRepository, "analyze", side_effect=analyze):
        screen = AppTest.from_file(Path("admin/eclado_admin/main.py").resolve()).run(timeout=30)
        assert not screen.exception
        screen.text_input[0].set_value("user@example.com")
        screen.text_input[1].set_value("x")
        screen.button[0].click().run(timeout=30)
        assert not screen.exception
        assert len(screen.radio) == 1
        assert screen.radio(key="sales_page").options == [
            "매출 요약",
            "매출 추이",
            "고객별 매출 추이",
            "매출·상품·리뷰 AI",
        ]
        assert screen.selectbox(key="sales_source").value == "업로드 더미 데이터"
        assert not screen.exception
        assert screen.metric[0].value == "45,000,000원"
        screen.selectbox(key="sales_source").select("실제 실적 · 연동 대기").run(timeout=30)
        assert all(metric.value != "45,000,000원" for metric in screen.metric)
        screen.button(key="open_saved_dummy").click().run(timeout=30)
        assert screen.selectbox(key="sales_source").value == "업로드 더미 데이터"
        assert screen.metric[0].value == "45,000,000원"
        screen.button(key="dummy_full_range").click().run(timeout=30)
        assert screen.date_input(key="sales_start_매출 요약").value == data.coverage_start
        assert screen.date_input(key="sales_end_매출 요약").value == data.coverage_end
        screen.radio(key="sales_page").set_value("매출 추이").run(timeout=30)
        assert not screen.exception
        assert screen.date_input(key="sales_start_매출 추이").value == date(2020, 1, 1)
        assert len(screen.tabs) == 3
        assert any("365일" in message.value for message in screen.caption)
        screen.radio(key="sales_page").set_value("고객별 매출 추이").run(timeout=30)
        assert not screen.exception
        assert "80대" in screen.selectbox[2].options
        screen.selectbox[1].select("여성").run(timeout=30)
        assert not screen.exception
        assert screen.metric[0].value == "22,500,000원"
        screen.selectbox[3].select("2회 이상 구매 고객").run(timeout=30)
        assert not screen.exception
        assert not screen.metric
        screen.radio(key="sales_page").set_value("매출·상품·리뷰 AI").run(timeout=30)
        assert not screen.exception
        assert any("긍정적 리뷰" in title.value for title in screen.subheader)


def test_sales_repository_passes_filters_and_typed_dummy_upload() -> None:
    class FakeClient:
        def get(self, path: str) -> dict[str, object]:
            assert path.startswith("/api/v1/sales/preview?source=dummy&start=2020-01-01")
            assert "gender=female" in path and "persona=repeat" in path
            return {
                "source": "dummy",
                "start": "2020-01-01",
                "end": "2020-01-31",
                "status": "input pending",
            }

        def post(self, path: str, payload: dict[str, object]) -> dict[str, object]:
            assert path == "/api/v1/sales/dummy"
            assert payload["synthetic"] is True
            return {
                "status": "imported",
                "customers": 0,
                "orders": 0,
                "items": 0,
                "dataset_hash": "fake",
            }

    repository = SalesRepository(FakeClient())
    result = repository.analyze(
        "dummy", date(2020, 1, 1), date(2020, 1, 31), gender="female", persona="repeat"
    )
    assert result.totals is None
    dataset = DummySalesDataset(
        schema_version="1",
        synthetic=True,
        coverage_start=date(2020, 1, 1),
        coverage_end=date(2020, 1, 31),
        customers=[],
        orders=[],
    )
    assert repository.import_dummy(dataset).status == "imported"
