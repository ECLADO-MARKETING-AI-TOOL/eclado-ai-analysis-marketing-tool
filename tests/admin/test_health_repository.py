from eclado_admin.repositories.health_repository import HealthRepository


class FakeApiClient:
    def get(self, path: str) -> dict[str, object]:
        assert path == "/api/v1/health"
        return {"status": "ok", "environment": "test"}


def test_health_repository_uses_api_client() -> None:
    result = HealthRepository(FakeApiClient()).get_health()

    assert result.status == "ok"
    assert result.environment == "test"