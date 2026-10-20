from collections.abc import Iterator
from unittest.mock import patch

import pytest
from tests.preview_session_fakes import MemoryPreviewSessionStore

from eclado_backend.services.preview_session_service import PreviewSessionService


@pytest.fixture(autouse=True)
def fake_preview_sessions() -> Iterator[None]:
    service = PreviewSessionService(MemoryPreviewSessionStore())
    with patch("eclado_admin.demo_auth.demo_sessions", return_value=service):
        yield
