from eclado_shared.api.client import ApiClient
from eclado_shared.schemas.preview_session import PreviewSession, PreviewSessionStatus


class PreviewSessionRepository:
    def __init__(self, client: ApiClient | None = None) -> None:
        self._client = client or ApiClient()

    def issue(self) -> tuple[str, float]:
        result = PreviewSession.model_validate(
            self._client.post("/api/v1/preview-auth/session", {})
        )
        return result.token, result.expires

    def expires_at(self, token: object) -> float | None:
        if not isinstance(token, str) or not 40 <= len(token) <= 100:
            return None
        result = PreviewSessionStatus.model_validate(
            self._client.get(
                "/api/v1/preview-auth/session", headers={"Authorization": f"Bearer {token}"}
            )
        )
        return result.expires

    def revoke(self, token: object) -> None:
        if isinstance(token, str):
            self._client.post(
                "/api/v1/preview-auth/logout", {}, headers={"Authorization": f"Bearer {token}"}
            )
