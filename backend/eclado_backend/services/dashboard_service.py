from datetime import date, timedelta
from typing import Literal

from eclado_backend.services.marketing_preview import MarketingAdvisor
from eclado_backend.stores.catalog_store import CatalogSnapshotStore
from eclado_backend.stores.dashboard_store import DashboardStore
from eclado_shared.schemas.dashboard import (
    CatalogEntry,
    CustomerOverview,
    DailySales,
    DashboardResponse,
    ProductPerformance,
    ProductSpecification,
    PurchaseRow,
    SalesTotals,
)


class DashboardService:
    def __init__(
        self,
        store: DashboardStore,
        advisor: MarketingAdvisor,
        catalog_store: CatalogSnapshotStore | None = None,
    ) -> None:
        self._store = store
        self._advisor = advisor
        self._catalog_store = catalog_store

    def get_dashboard(
        self, start: date, end: date, source: Literal["demo", "pending"]
    ) -> DashboardResponse:
        result = DashboardResponse(
            source=source,
            start=start,
            end=end,
            status="데이터 연동 대기" if source == "pending" else "가상 데이터 · 화면 검토용",
            metric_policy=(
                "데모 산식: 결제일 기준, 상품 할인 차감, 환불 완료일 차감. "
                "배송비 별도 / 실제 매출 정책 승인 대기 / AOV 미확정"
            ),
        )
        if self._catalog_store is not None:
            catalog = self._catalog_store.load()
            specifications = self._catalog_store.load_specifications()
            result.specification_source = specifications.source_file
            result.catalog_status = (
                "공개 상품 목록 수집 완료" if catalog.complete else "공개 상품 목록 일부 수집"
            )
            result.catalog_observed_at = catalog.observed_at
            for catalog_product in catalog.products:
                observation = catalog_product.observations[0]
                entry = CatalogEntry(
                    product_id=catalog_product.product_id,
                    name=catalog_product.name,
                    url=catalog_product.url,
                    sale_price=observation.sale_price,
                    discounted_price=observation.discounted_price,
                    list_price=observation.list_price,
                    price_source=observation.source_url,
                    observed_at=observation.observed_at,
                    price_conflict=len(
                        {
                            (row.sale_price, row.discounted_price, row.list_price)
                            for row in catalog_product.observations
                        }
                    )
                    > 1,
                )
                match = specifications.products.get(catalog_product.product_id)
                if match is not None and match.catalog_name == catalog_product.name:
                    entry.specifications = [
                        ProductSpecification(
                            capacity=variant.capacity,
                            ean=variant.ean,
                            source_name=variant.english_name,
                            source_row=variant.source_row,
                        )
                        for variant in match.variants
                    ]
                    entry.specification_note = match.note
                else:
                    entry.specification_note = "엑셀과 상품 연결 확인 필요"
                result.catalog.append(entry)
        if source == "pending":
            return result
        data = self._store.load()
        items = [item for item in data.items if start <= item.paid_on <= end]
        refunds = [refund for refund in data.refunds if start <= refund.completed_on <= end]
        reviews = [review for review in data.reviews if start <= review.created_on <= end]
        gross = sum(item.quantity * item.unit_price for item in items)
        discounts = sum(item.discount for item in items)
        refund_total = sum(refund.amount for refund in refunds)
        buyers = {item.customer_id for item in items}
        result.totals = SalesTotals(
            gross=gross,
            discounts=discounts,
            refunds=refund_total,
            net=gross - discounts - refund_total,
            shipping=sum(item.shipping for item in items),
            orders=len({item.order_id for item in items}),
            buyers=len(buyers),
        )
        for offset in range((end - start).days + 1):
            day = start + timedelta(days=offset)
            day_refunds = sum(refund.amount for refund in refunds if refund.completed_on == day)
            net = (
                sum(
                    item.quantity * item.unit_price - item.discount
                    for item in items
                    if item.paid_on == day
                )
                - day_refunds
            )
            result.daily.append(DailySales(day=day, net=net, refunds=day_refunds))
        for product in data.products:
            product_items = [item for item in items if item.product_id == product.id]
            product_refunds = [refund for refund in refunds if refund.product_id == product.id]
            ratings = [review.rating for review in reviews if review.product_id == product.id]
            result.products.append(
                ProductPerformance(
                    product_id=product.id,
                    name=product.name,
                    units=sum(item.quantity for item in product_items)
                    - sum(refund.quantity for refund in product_refunds),
                    net=sum(
                        item.quantity * item.unit_price - item.discount for item in product_items
                    )
                    - sum(refund.amount for refund in product_refunds),
                    review_count=len(ratings),
                    average_rating=round(sum(ratings) / len(ratings), 2) if ratings else None,
                )
            )
        first_dates = {
            buyer: min(item.paid_on for item in data.items if item.customer_id == buyer)
            for buyer in buyers
        }
        first_buyers = sum(first >= start for first in first_dates.values())
        result.customers = CustomerOverview(
            buyers=len(buyers),
            first_time_buyers=first_buyers,
            returning_buyers=len(buyers) - first_buyers,
            repeat_order_buyers=sum(
                len({item.order_id for item in items if item.customer_id == buyer}) >= 2
                for buyer in buyers
            ),
        )
        names = {product.id: product.name for product in data.products}
        result.purchases = [
            PurchaseRow(
                order_id=item.order_id,
                paid_on=item.paid_on,
                product=names[item.product_id],
                quantity=item.quantity,
                amount=item.quantity * item.unit_price - item.discount,
            )
            for item in sorted(items, key=lambda item: item.paid_on, reverse=True)
        ]
        best = max(result.products, key=lambda product: product.units, default=None)
        result.summary = [
            f"선택 기간 순상품매출 {result.totals.net:,}원, "
            f"결제 주문 {result.totals.orders}건입니다.",
            f"상품 환불 {refund_total:,}원을 완료일 기준으로 반영했습니다.",
            f"구매 고객 {len(buyers)}명 중 이전 구매 이력이 있는 고객은 "
            f"{result.customers.returning_buyers}명입니다.",
        ]
        if best:
            result.summary.append(f"순판매 수량 1위는 {best.name} ({best.units}개)입니다.")
        result.recommendations = self._advisor.recommend(result.products)
        return result
