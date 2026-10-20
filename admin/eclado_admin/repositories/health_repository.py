from eclado_shared.api.client import ApiClient
from eclado_shared.schemas.health import HealthResponse


class HealthRepository:
    def __init__(self, client: ApiClient | None = None) -> None:
        self._client = client or ApiClient()

    def get_health(self) -> HealthResponse:
        response = self._client.get("/api/v1/health")
        return HealthResponse.model_validate(response)
