from fastapi import APIRouter

from eclado_backend.schemas.health_schema import HealthResponse
from eclado_backend.services.health_service import HealthService
from eclado_backend.stores.health_store import HealthStore

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    result = HealthService(HealthStore()).get_status()
    return HealthResponse(**result)
