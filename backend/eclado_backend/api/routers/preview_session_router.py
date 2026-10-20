"""Preview UI session continuity only, not authorization for business APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header

from eclado_backend.services.preview_session_service import PreviewSessionService
from eclado_backend.stores.preview_session_store import LocalPreviewSessionStore
from eclado_shared.schemas.preview_session import PreviewSession, PreviewSessionStatus

router = APIRouter()


def get_session_store() -> LocalPreviewSessionStore:
    return LocalPreviewSessionStore()


@router.post("/preview-auth/session")
def issue_session(
    store: Annotated[LocalPreviewSessionStore, Depends(get_session_store)],
) -> PreviewSession:
    token, expires = PreviewSessionService(store).issue()
    return PreviewSession(token=token, expires=expires)


@router.get("/preview-auth/session")
def session_status(
    store: Annotated[LocalPreviewSessionStore, Depends(get_session_store)],
    authorization: Annotated[str | None, Header()] = None,
) -> PreviewSessionStatus:
    token = authorization.removeprefix("Bearer ") if authorization else None
    return PreviewSessionStatus(expires=PreviewSessionService(store).expires_at(token))


@router.post("/preview-auth/logout")
def revoke_session(
    store: Annotated[LocalPreviewSessionStore, Depends(get_session_store)],
    authorization: Annotated[str | None, Header()] = None,
) -> PreviewSessionStatus:
    token = authorization.removeprefix("Bearer ") if authorization else None
    PreviewSessionService(store).revoke(token)
    return PreviewSessionStatus()
