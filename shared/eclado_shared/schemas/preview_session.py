from pydantic import BaseModel


class PreviewSession(BaseModel):
    token: str
    expires: float


class PreviewSessionStatus(BaseModel):
    expires: float | None = None
