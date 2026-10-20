"""Preview session persistence is accessed through the backend repository."""

from eclado_admin.repositories.preview_session_repository import PreviewSessionRepository


def demo_sessions() -> PreviewSessionRepository:
    return PreviewSessionRepository()
