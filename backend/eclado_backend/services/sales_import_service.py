from collections import Counter
from datetime import date

from eclado_backend.stores.sales_store import SalesStore
from eclado_shared.schemas.sales import DummyImportResult, DummySalesDataset


class SalesImportService:
    def __init__(self, store: SalesStore, product_ids: set[str]) -> None:
        self._store = store
        self._product_ids = product_ids

    def import_dataset(self, dataset: DummySalesDataset) -> DummyImportResult:
        self.validate(dataset)
        changed, digest = self._store.save(dataset)
        return DummyImportResult(
            status="imported" if changed else "unchanged",
            customers=len(dataset.customers),
            orders=len(dataset.orders),
            items=sum(len(order.items) for order in dataset.orders),
            dataset_hash=digest,
            reviews=len(dataset.reviews),
        )

    def validate(self, dataset: DummySalesDataset) -> None:
        if not date(2020, 1, 1) <= dataset.coverage_start <= dataset.coverage_end:
            raise ValueError("데이터 범위는 2020-01-01 이후이며 종료일이 시작일 이후여야 합니다.")
        customers = {customer.customer_id: customer for customer in dataset.customers}
        if len(customers) != len(dataset.customers):
            raise ValueError("중복 고객 ID가 있습니다.")
        orders = {order.order_id: order for order in dataset.orders}
        for product_id, launched in dataset.product_launch_dates.items():
            if product_id not in self._product_ids or launched > dataset.coverage_end:
                raise ValueError("상품 출시일의 상품 연결·일자를 확인해 주세요.")
        for order in dataset.orders:
            for item in order.items:
                item_launched = dataset.product_launch_dates.get(item.product_id)
                if item_launched is not None and item_launched > order.paid_on:
                    raise ValueError("상품 출시일보다 앞선 구매 항목이 있습니다.")
        if len(orders) != len(dataset.orders):
            raise ValueError("중복 주문 ID가 있습니다.")
        if sum(len(order.items) for order in dataset.orders) > 100000:
            raise ValueError("상품 항목은 최대 100,000건입니다.")
        for order in dataset.orders:
            if order.customer_id not in customers:
                raise ValueError("연결되지 않은 고객 ID가 있습니다.")
            if not dataset.coverage_start <= order.paid_on <= dataset.coverage_end:
                raise ValueError("범위 밖 결제일이 있습니다.")
            birth = customers[order.customer_id].birth_year
            if birth is not None and birth > order.paid_on.year:
                raise ValueError("출생연도가 결제연도보다 늦습니다.")
            if len({item.item_id for item in order.items}) != len(order.items):
                raise ValueError("주문 내 항목 ID가 중복되었습니다.")
            for item in order.items:
                if item.product_id not in self._product_ids:
                    raise ValueError("카탈로그에 없는 상품 ID가 있습니다.")
                if item.discount > item.quantity * item.unit_price:
                    raise ValueError("할인이 구매 상품금액을 초과합니다.")
        if len({refund.refund_id for refund in dataset.refunds}) != len(dataset.refunds):
            raise ValueError("환불 ID가 중복되었습니다.")
        if len({review.review_id for review in dataset.reviews}) != len(dataset.reviews):
            raise ValueError("리뷰 ID가 중복되었습니다.")
        reviewed_items: set[tuple[str, str]] = set()
        for review in dataset.reviews:
            review_order = orders.get(review.order_id)
            key = (review.order_id, review.item_id)
            if (
                review_order is None
                or review.customer_id != review_order.customer_id
                or not any(item.item_id == review.item_id for item in review_order.items)
                or not review_order.paid_on <= review.created_on <= dataset.coverage_end
                or key in reviewed_items
            ):
                raise ValueError("리뷰 고객·구매 항목·작성일·중복 여부를 확인해 주세요.")
            reviewed_items.add(key)
        amounts: Counter[tuple[str, str]] = Counter()
        quantities: Counter[tuple[str, str]] = Counter()
        shipping: Counter[str] = Counter()
        for refund in dataset.refunds:
            refund_order = orders.get(refund.order_id)
            refund_item = (
                next((row for row in refund_order.items if row.item_id == refund.item_id), None)
                if refund_order
                else None
            )
            if refund_order is None or refund_item is None:
                raise ValueError("원주문·항목에 연결되지 않은 환불이 있습니다.")
            if not refund_order.paid_on <= refund.completed_on <= dataset.coverage_end:
                raise ValueError("환불 완료일이 결제일 이전이거나 데이터 범위 밖입니다.")
            key = (refund.order_id, refund.item_id)
            amounts[key] += refund.amount
            quantities[key] += refund.quantity
            shipping[refund.order_id] += refund.shipping_refund
            if (
                amounts[key] > refund_item.quantity * refund_item.unit_price - refund_item.discount
                or quantities[key] > refund_item.quantity
                or shipping[refund.order_id] > refund_order.shipping
            ):
                raise ValueError("누적 환불 금액·수량·배송비가 원거래를 초과합니다.")
