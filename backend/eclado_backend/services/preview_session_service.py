from hashlib import sha256
from secrets import token_urlsafe
from time import time

from eclado_backend.stores.preview_session_store import PreviewSessionStore

SESSION_SECONDS = 3600


class PreviewSessionService:
    def __init__(self, store: PreviewSessionStore) -> None:
        self._store = store

    def issue(self) -> tuple[str, float]:
        now = time()
        token = token_urlsafe(32)
        expires = now + SESSION_SECONDS
        self._store.save(sha256(token.encode()).hexdigest(), expires, now)
        return token, expires

    def expires_at(self, token: object) -> float | None:
        if not isinstance(token, str) or not 40 <= len(token) <= 100:
            return None
        expires = self._store.expires_at(sha256(token.encode()).hexdigest())
        return expires if expires is not None and expires > time() else None

    def revoke(self, token: object) -> None:
        if isinstance(token, str):
            self._store.revoke(sha256(token.encode()).hexdigest())
