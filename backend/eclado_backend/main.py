from fastapi import FastAPI

from eclado_backend.api.routers.dashboard_router import router as dashboard_router
from eclado_backend.api.routers.health_router import router as health_router
from eclado_backend.api.routers.preview_session_router import router as preview_session_router
from eclado_backend.api.routers.sales_router import router as sales_router

app = FastAPI(title="Eclado Marketing AI API", version="0.1.0")
app.include_router(health_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")
app.include_router(preview_session_router, prefix="/api/v1")
