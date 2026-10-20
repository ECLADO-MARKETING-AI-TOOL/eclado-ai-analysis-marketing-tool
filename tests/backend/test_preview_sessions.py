from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from tests.preview_session_fakes import MemoryPreviewSessionStore

from eclado_backend.api.routers.preview_session_router import get_session_store
from eclado_backend.main import app
from eclado_backend.services.preview_session_service import PreviewSessionService
from eclado_backend.stores.preview_session_store import LocalPreviewSessionStore


def test_persistent_sessions_survive_new_store_and_service_until_absolute_expiry() -> None:
    path = Path.cwd() / ".cache" / f"test-preview-session-{uuid4().hex}.sqlite3"
    try:
        with patch("eclado_backend.services.preview_session_service.time", return_value=1000):
            first = PreviewSessionService(LocalPreviewSessionStore(path))
            token, expiry = first.issue()
            assert expiry == 4600
        with patch("eclado_backend.services.preview_session_service.time", return_value=4599):
            restarted = PreviewSessionService(LocalPreviewSessionStore(path))
            assert restarted.expires_at(token) == expiry
            assert token.encode() not in path.read_bytes()  # Only hashes are persisted.
        with patch("eclado_backend.services.preview_session_service.time", return_value=4600):
            assert PreviewSessionService(LocalPreviewSessionStore(path)).expires_at(token) is None
        restarted.revoke(token)
        with patch("eclado_backend.services.preview_session_service.time", return_value=4599):
            assert PreviewSessionService(LocalPreviewSessionStore(path)).expires_at(token) is None
    finally:
        path.unlink(missing_ok=True)


def test_session_api_issues_validates_and_revokes_without_url_tokens() -> None:
    store = MemoryPreviewSessionStore()
    app.dependency_overrides[get_session_store] = lambda: store
    try:
        client = TestClient(app)
        issued = client.post("/api/v1/preview-auth/session").json()
        headers = {"Authorization": "Bearer " + issued["token"]}
        assert client.get("/api/v1/preview-auth/session", headers=headers).json() == {
            "expires": issued["expires"]
        }
        assert client.get("/api/v1/preview-auth/session").json() == {"expires": None}
        assert client.post("/api/v1/preview-auth/logout", headers=headers).status_code == 200
        assert client.get("/api/v1/preview-auth/session", headers=headers).json() == {
            "expires": None
        }
    finally:
        app.dependency_overrides.clear()
