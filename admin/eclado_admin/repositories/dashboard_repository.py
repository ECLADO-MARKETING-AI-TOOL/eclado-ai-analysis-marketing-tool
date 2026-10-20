from datetime import date
from typing import Literal, Protocol
from urllib.parse import urlencode

from eclado_shared.api.client import ApiClient
from eclado_shared.schemas.dashboard import DashboardResponse


class DashboardApiClient(Protocol):
    def get(self, path: str) -> dict[str, object]: ...


class DashboardRepository:
    def __init__(self, client: DashboardApiClient | None = None) -> None:
        self._client = client or ApiClient()

    def get_dashboard(
        self, source: Literal["demo", "pending"], start: date, end: date
    ) -> DashboardResponse:
        query = urlencode({"source": source, "start": start.isoformat(), "end": end.isoformat()})
        return DashboardResponse.model_validate(
            self._client.get(f"/api/v1/dashboard/preview?{query}")
        )
