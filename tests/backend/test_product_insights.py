from datetime import date, timedelta

from eclado_backend.services.product_insights_service import populate_insights
from eclado_backend.services.sales_service import Event
from eclado_shared.schemas.sales import (
    DummyCustomer,
    DummyItem,
    DummyOrder,
    DummyReview,
    DummySalesDataset,
    SalesAnalysis,
)


def test_monthly_ten_percent_boundary_new_product_exclusion_and_unknown_launch() -> None:
    end = date(2026, 10, 20)
    data = DummySalesDataset(
        schema_version="1",
        synthetic=True,
        coverage_start=end - timedelta(days=59),
        coverage_end=end,
        customers=[],
        orders=[],
        product_launch_dates={"11": end - timedelta(days=30), "12": end - timedelta(days=100)},
    )
    rows = []
    for product in ["11", "12", "13", "14", "15"]:
        for i in range(5):
            for offset, amount, units in [(40, 1000, 10), (0, 1100, 11)]:
                if product == "14" and offset == 0:
                    amount = 900
                if product == "15" and offset == 0:
                    amount = 1099  # Just below the 10% threshold.
                rows.append(
                    Event(
                        end - timedelta(days=offset),
                        f"dummy-c-{i}",
                        product,
                        f"dummy-o-{product}-{i}",
                        "female",
                        "30대",
                        paid=amount,
                        units=units,
                        payment=True,
                    )
                )
    result = SalesAnalysis(source="dummy", start=end, end=end, status="test")
    populate_insights(result, data, rows, {str(i): str(i) for i in range(11, 16)})
    changes = {row.product_id: row for row in result.monthly_product_changes}
    assert result.change_history_complete
    assert "11" not in changes  # Exactly 30 days is still new.
    assert "15" not in changes
    assert changes["12"].launch_status == "established"
    assert changes["12"].percent == 10
    assert changes["12"].units_delta == 5 and changes["12"].units_percent == 10
    assert changes["13"].launch_status == "unknown"
    assert changes["14"].percent == -10
    # All products together average below threshold; no invented age alert.
    assert not result.monthly_age_changes
    data.coverage_start += timedelta(days=1)
    incomplete = SalesAnalysis(source="dummy", start=end, end=end, status="test")
    populate_insights(incomplete, data, rows, {str(i): str(i) for i in range(11, 16)})
    assert not incomplete.change_history_complete and not incomplete.monthly_product_changes


def test_review_surges_top_ten_zero_baseline_and_age_privacy() -> None:
    end = date(2026, 10, 20)
    data = DummySalesDataset(
        schema_version="1",
        synthetic=True,
        coverage_start=end - timedelta(days=90),
        coverage_end=end,
        customers=[DummyCustomer(customer_id="dummy-c")],
        orders=[],
    )
    events = []
    names = {}
    for i in range(12):
        product = str(i + 11)
        names[product] = product
        oid = f"dummy-o-{i}"
        itemid = f"dummy-i-{i}"
        data.orders.append(
            DummyOrder(
                order_id=oid,
                customer_id="dummy-c",
                paid_on=end - timedelta(days=20),
                items=[DummyItem(item_id=itemid, product_id=product, quantity=1, unit_price=1000)],
            )
        )
        data.reviews.append(
            DummyReview(
                review_id=f"dummy-r-{i}",
                customer_id="dummy-c",
                order_id=oid,
                item_id=itemid,
                created_on=end,
                rating=5,
                text="synthetic",
            )
        )
        events += [
            Event(
                end - timedelta(days=40),
                "dummy-c",
                product,
                oid,
                "female",
                "80대",
                paid=1000,
                units=1,
                payment=True,
            ),
            Event(end, "dummy-c", product, oid, "female", "80대", paid=2000, units=2, payment=True),
        ]
    result = SalesAnalysis(source="dummy", start=end, end=end, status="test")
    populate_insights(result, data, events, names)
    assert len(result.review_rises) == 10
    assert all(row.percent is None and row.delta == 1 for row in result.review_rises)
    assert not result.monthly_age_changes  # One customer cannot expose an age cohort.
