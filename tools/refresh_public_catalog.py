"""Run explicitly to refresh public product names/prices, never on a page view."""

from eclado_backend.services.public_catalog import HttpPublicPageClient, collect_public_catalog
from eclado_backend.stores.catalog_store import CatalogSnapshotStore


def main() -> None:
    snapshot = collect_public_catalog(HttpPublicPageClient())
    CatalogSnapshotStore().save(snapshot)
    print(f"Saved {len(snapshot.products)} products; complete={snapshot.complete}")
    if snapshot.errors:
        print("Collection incomplete; inspect snapshot errors before claiming full coverage")


if __name__ == "__main__":
    main()
