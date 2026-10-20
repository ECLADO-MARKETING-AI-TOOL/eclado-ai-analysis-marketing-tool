from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException

from eclado_backend.services.dashboard_service import DashboardService
from eclado_backend.services.marketing_preview import RulePreviewAdvisor
from eclado_backend.stores.catalog_store import CatalogSnapshotStore
from eclado_backend.stores.dashboard_store import DEMO_END, DemoDashboardStore
from eclado_shared.schemas.dashboard import DashboardResponse

router = APIRouter()


@router.get("/dashboard/preview", response_model=DashboardResponse)
def dashboard_preview(
    source: Literal["demo", "pending"] = "pending",
    start: date = DEMO_END - timedelta(days=29),
    end: date = DEMO_END,
) -> DashboardResponse:
    if end < start or (end - start).days >= 366:
        raise HTTPException(status_code=422, detail="기간은 시작일 이후 최대 366일입니다.")
    if source == "demo" and (start < DEMO_END - timedelta(days=44) or end > DEMO_END):
        raise HTTPException(status_code=422, detail="데모 제공 기간 밖입니다.")
    return DashboardService(
        DemoDashboardStore(), RulePreviewAdvisor(), CatalogSnapshotStore()
    ).get_dashboard(start, end, source)
