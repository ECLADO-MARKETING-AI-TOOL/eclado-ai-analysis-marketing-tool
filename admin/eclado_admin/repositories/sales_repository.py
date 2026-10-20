from datetime import date
from typing import Protocol
from urllib.parse import urlencode

from eclado_shared.api.client import ApiClient
from eclado_shared.schemas.sales import (
    DummyImportResult,
    DummySalesDataset,
    Persona,
    SalesAnalysis,
    Source,
)


class SalesApiClient(Protocol):
    def get(self, path: str) -> dict[str, object]: ...
    def post(self, path: str, payload: dict[str, object]) -> dict[str, object]: ...


class SalesRepository:
    def __init__(self, client: SalesApiClient | None = None) -> None:
        self._client = client or ApiClient()

    def analyze(
        self,
        source: Source,
        start: date,
        end: date,
        gender: str = "all",
        age: str = "전체",
        persona: Persona = "all",
        alert_percent: float = 50,
        min_change: int = 100000,
    ) -> SalesAnalysis:
        query = urlencode(
            {
                "source": source,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "gender": gender,
                "age": age,
                "persona": persona,
                "alert_percent": alert_percent,
                "min_change": min_change,
            }
        )
        return SalesAnalysis.model_validate(self._client.get(f"/api/v1/sales/preview?{query}"))

    def import_dummy(self, dataset: DummySalesDataset) -> DummyImportResult:
        return DummyImportResult.model_validate(
            self._client.post("/api/v1/sales/dummy", dataset.model_dump(mode="json"))
        )
