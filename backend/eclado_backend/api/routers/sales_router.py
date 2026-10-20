from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from eclado_backend.services.sales_import_service import SalesImportService
from eclado_backend.services.sales_service import AGE_BANDS, SalesAnalysisService
from eclado_backend.stores.catalog_store import CatalogSnapshotStore
from eclado_backend.stores.sales_store import LocalDummySalesStore, demo_sales_dataset
from eclado_shared.schemas.sales import (
    DummyImportResult,
    DummySalesDataset,
    Persona,
    SalesAnalysis,
    Source,
)

router = APIRouter()


def get_dummy_store() -> LocalDummySalesStore:
    return LocalDummySalesStore()


def current_business_day() -> date:
    return (datetime.now(UTC) + timedelta(hours=9)).date()


@router.get("/sales/preview", response_model=SalesAnalysis)
def sales_preview(
    store: Annotated[LocalDummySalesStore, Depends(get_dummy_store)],
    source: Source = "pending",
    start: date = date(2020, 1, 1),
    end: date | None = None,
    gender: Literal["all", "male", "female", "unknown"] = "all",
    age: str = "전체",
    persona: Persona = "all",
    alert_percent: Annotated[float, Query(ge=1, le=1000)] = 50,
    min_change: Annotated[int, Query(ge=0, le=1000000000)] = 100000,
) -> SalesAnalysis:
    end = end or current_business_day()
    if not date(2020, 1, 1) <= start <= end <= current_business_day():
        raise HTTPException(status_code=422, detail="조회 기간은 2020-01-01부터 오늘까지입니다.")
    if age not in ["전체", *AGE_BANDS]:
        raise HTTPException(status_code=422, detail="지원하지 않는 연령대입니다.")
    names = {row.product_id: row.name for row in CatalogSnapshotStore().load().products}
    try:
        dataset = (
            demo_sales_dataset()
            if source == "demo"
            else store.load()
            if source == "dummy"
            else None
        )
        if dataset is not None:
            SalesImportService(store, set(names)).validate(dataset)
        return SalesAnalysisService(names).analyze(
            dataset, source, start, end, gender, age, persona, alert_percent, min_change
        )
    except (ValueError, KeyError) as error:
        raise HTTPException(status_code=422, detail="데이터 연결·형식을 확인해 주세요.") from error


@router.post("/sales/dummy", response_model=DummyImportResult)
def import_dummy_sales(
    dataset: DummySalesDataset,
    store: Annotated[LocalDummySalesStore, Depends(get_dummy_store)],
) -> DummyImportResult:
    ids = {row.product_id for row in CatalogSnapshotStore().load().products}
    if dataset.coverage_end > current_business_day():
        raise HTTPException(status_code=422, detail="미래 데이터는 업로드할 수 없습니다.")
    try:
        return SalesImportService(store, ids).import_dataset(dataset)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/sales/dummy/schema")
def dummy_schema() -> dict[str, object]:
    return DummySalesDataset.model_json_schema()
