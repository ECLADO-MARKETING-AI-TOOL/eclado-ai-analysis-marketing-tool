import httpx
from pydantic import TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    api_base_url: str = "http://127.0.0.1:8000"
    model_config = SettingsConfigDict(env_prefix="ECLADO_", env_file=".env", extra="ignore")


class ApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        settings = ApiSettings()
        self._base_url = (base_url or settings.api_base_url).rstrip("/")

    def get(self, path: str, *, headers: dict[str, str] | None = None) -> dict[str, object]:
        response = httpx.get(
            f"{self._base_url}{path}", headers=headers, timeout=10.0, trust_env=False
        )
        response.raise_for_status()
        return TypeAdapter(dict[str, object]).validate_python(response.json())

    def post(
        self, path: str, payload: dict[str, object], *, headers: dict[str, str] | None = None
    ) -> dict[str, object]:
        response = httpx.post(
            f"{self._base_url}{path}", json=payload, headers=headers, timeout=30, trust_env=False
        )
        response.raise_for_status()
        return TypeAdapter(dict[str, object]).validate_python(response.json())
