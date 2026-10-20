from eclado_backend.stores.health_store import HealthStore


class HealthService:
    def __init__(self, store: HealthStore) -> None:
        self._store = store

    def get_status(self) -> dict[str, str]:
        return self._store.get_status()
