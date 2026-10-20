from pathlib import Path

from eclado_backend.schemas.catalog_schema import CatalogSnapshot
from eclado_backend.schemas.product_specification import ProductSpecificationReference

CATALOG_PATH = Path(__file__).parent / "data" / "public_catalog.json"


class CatalogSnapshotStore:
    def load_specifications(self) -> ProductSpecificationReference:
        path = CATALOG_PATH.with_name("product_specifications.json")
        return ProductSpecificationReference.model_validate_json(path.read_text(encoding="utf-8"))

    def load(self) -> CatalogSnapshot:
        return CatalogSnapshot.model_validate_json(CATALOG_PATH.read_text(encoding="utf-8"))

    def save(self, snapshot: CatalogSnapshot) -> None:
        if not snapshot.products:
            raise ValueError("Empty collection must not replace the catalog")
        CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Preserve every observation as a dated artifact; latest is a local preview pointer.
        stamp = snapshot.observed_at.strftime("%Y%m%dT%H%M%SZ")
        serialized = snapshot.model_dump_json(indent=2)
        archive = CATALOG_PATH.with_name(f"catalog-{stamp}.json")
        with archive.open("x", encoding="utf-8") as output:
            output.write(serialized)
        CATALOG_PATH.write_text(serialized, encoding="utf-8")
