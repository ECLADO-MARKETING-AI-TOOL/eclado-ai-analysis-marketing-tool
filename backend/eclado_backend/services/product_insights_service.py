"""Evidence-based preview comparisons, independent of external AI providers."""

from collections import defaultdict
from datetime import timedelta
from typing import TYPE_CHECKING, Literal

from eclado_shared.schemas.sales import DummySalesDataset, MonthlyChange, ReviewRise, SalesAnalysis

if TYPE_CHECKING:
    from eclado_backend.services.sales_service import Event


def populate_insights(
    result: SalesAnalysis, data: DummySalesDataset, events: list[Event], names: dict[str, str]
) -> None:
    end = result.end
    first = end - timedelta(days=59)
    midpoint = end - timedelta(days=29)
    result.change_history_complete = data.coverage_start <= first and end <= data.coverage_end
    if result.change_history_complete:
        for attribute in ("product", "age_band"):
            groups: dict[str, list[Event]] = defaultdict(list)
            for event in events:
                if first <= event.day <= end:
                    groups[getattr(event, attribute)].append(event)
            for key, rows in groups.items():
                before = [row for row in rows if row.day < midpoint]
                after = [row for row in rows if row.day >= midpoint]
                if attribute == "age_band" and (
                    len({row.customer for row in before}) < 5
                    or len({row.customer for row in after}) < 5
                ):
                    continue
                previous = sum(row.net for row in before)
                current = sum(row.net for row in after)
                # A zero or negative baseline has no meaningful relative increase.
                if previous <= 0 or abs(current - previous) * 100 < previous * 10:
                    continue
                previous_units = sum(row.units for row in before if row.payment)
                current_units = sum(row.units for row in after if row.payment)
                status: Literal["established", "new", "unknown"] = "established"
                if attribute == "product":
                    launched = data.product_launch_dates.get(key)
                    status = (
                        "unknown"
                        if launched is None
                        else ("new" if (end - launched).days <= 30 else "established")
                    )
                change = MonthlyChange(
                    label=names[key] if attribute == "product" else key,
                    product_id=key if attribute == "product" else None,
                    previous=previous,
                    current=current,
                    previous_average=previous / 30,
                    current_average=current / 30,
                    delta=current - previous,
                    percent=100 * (current - previous) / previous,
                    previous_units=previous_units,
                    current_units=current_units,
                    units_delta=current_units - previous_units,
                    units_percent=100 * (current_units - previous_units) / previous_units
                    if previous_units
                    else None,
                    launch_status=status,
                )
                if attribute == "product" and status != "new":
                    result.monthly_product_changes.append(change)
                elif attribute == "age_band":
                    result.monthly_age_changes.append(change)
        result.monthly_product_changes.sort(key=lambda row: (-abs(row.percent), row.label))
        result.monthly_age_changes.sort(key=lambda row: (-abs(row.percent), row.label))
    if data.coverage_start > end - timedelta(days=13) or end > data.coverage_end:
        return
    orders = {order.order_id: order for order in data.orders}
    eligible = {row.order for row in events if row.payment}
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for review in data.reviews:
        if (
            review.order_id not in eligible
            or not end - timedelta(days=13) <= review.created_on <= end
        ):
            continue
        order = orders[review.order_id]
        item = next(row for row in order.items if row.item_id == review.item_id)
        counts[item.product_id][int(review.created_on >= end - timedelta(days=6))] += 1
    result.review_rises = sorted(
        [
            ReviewRise(
                product_id=key,
                name=names[key],
                previous=values[0],
                current=values[1],
                delta=values[1] - values[0],
                percent=100 * (values[1] - values[0]) / values[0] if values[0] else None,
            )
            for key, values in counts.items()
            if values[1] > values[0]
        ],
        key=lambda row: (-row.delta, -row.current, row.product_id),
    )[:10]
