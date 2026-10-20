class MemoryPreviewSessionStore:
    def __init__(self) -> None:
        self.values: dict[str, float] = {}

    def save(self, digest: str, expires: float, now: float) -> None:
        self.values = {key: value for key, value in self.values.items() if value > now}
        self.values[digest] = expires

    def expires_at(self, digest: str) -> float | None:
        return self.values.get(digest)

    def revoke(self, digest: str) -> None:
        self.values.pop(digest, None)
