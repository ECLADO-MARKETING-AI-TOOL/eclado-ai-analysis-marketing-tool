from datetime import date

from eclado_backend.schemas.product_specification import SpecificationSourceRow
from eclado_backend.services.dashboard_service import DashboardService
from eclado_backend.services.marketing_preview import RulePreviewAdvisor
from eclado_backend.stores.catalog_store import CatalogSnapshotStore
from eclado_backend.stores.dashboard_store import DemoDashboardStore


def test_capacity_specific_eans_are_not_collapsed_or_cross_assigned() -> None:
    reference = CatalogSnapshotStore().load_specifications()
    cell_memory = reference.products["67"]
    assert [(row.capacity, row.ean) for row in cell_memory.variants] == [
        ("30g", "8809820610091"),
        ("50g", "8809820610947"),
        ("200g", "8809820611388"),
    ]
    cleanser = reference.products["13"]
    assert [(row.capacity, row.ean) for row in cleanser.variants] == [
        ("500ml", "8809085952523"),
        ("1000ml", "8809820611289"),
    ]
    assert reference.products["38"].variants == []  # ml/g conflict
    assert reference.products["161"].variants == []  # device+cream bundle != device
    assert [row.capacity for row in reference.products["59"].variants] == ["33g"]
    assert reference.products["59"].note
    assert "원본 확인" in (reference.products["157"].note or "")


def test_metadata_enrichment_preserves_all_catalog_prices() -> None:
    store = CatalogSnapshotStore()
    original = store.load()
    response = DashboardService(DemoDashboardStore(), RulePreviewAdvisor(), store).get_dashboard(
        date(2026, 10, 1), date(2026, 10, 20), "pending"
    )
    assert len(response.catalog) == len(original.products)
    for raw, enriched in zip(original.products, response.catalog, strict=True):
        price = raw.observations[0]
        assert raw.product_id == enriched.product_id
        assert (enriched.sale_price, enriched.discounted_price, enriched.list_price) == (
            price.sale_price,
            price.discounted_price,
            price.list_price,
        )
        assert enriched.observed_at == price.observed_at
        assert "categories" not in enriched.model_dump()
    assert store.load().model_dump() == original.model_dump()


def test_ean_is_text_and_preserves_leading_zero() -> None:
    row = SpecificationSourceRow(
        source_row=1, english_name="Test", capacity="10ml", ean="0123456789012"
    )
    assert row.ean == "0123456789012"
