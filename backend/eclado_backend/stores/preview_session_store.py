"""Durable, local-only preview token hashes; no customer data or passwords."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

SESSION_PATH = Path(__file__).resolve().parents[3] / ".local" / "preview_sessions.sqlite3"


class PreviewSessionStore(Protocol):
    def save(self, digest: str, expires: float, now: float) -> None: ...
    def expires_at(self, digest: str) -> float | None: ...
    def revoke(self, digest: str) -> None: ...


class LocalPreviewSessionStore:
    def __init__(self, path: Path = SESSION_PATH) -> None:
        self._path = path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._path)
        try:
            with connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS preview_sessions "
                    "(digest TEXT PRIMARY KEY, expires REAL NOT NULL)"
                )
                yield connection
        finally:
            connection.close()

    def save(self, digest: str, expires: float, now: float) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM preview_sessions WHERE expires <= ?", (now,))
            connection.execute("INSERT INTO preview_sessions VALUES (?, ?)", (digest, expires))

    def expires_at(self, digest: str) -> float | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT expires FROM preview_sessions WHERE digest = ?", (digest,)
            ).fetchone()
            return float(row[0]) if row else None

    def revoke(self, digest: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM preview_sessions WHERE digest = ?", (digest,))
