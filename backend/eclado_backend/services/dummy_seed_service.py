"""Deterministic synthetic test scenarios; never a source of real sales."""

from datetime import date, timedelta
from random import Random

from eclado_shared.schemas.dashboard import CatalogEntry
from eclado_shared.schemas.sales import (
    DummyCustomer,
    DummyItem,
    DummyOrder,
    DummyRefund,
    DummyReview,
    DummySalesDataset,
)

REGIONS = [
    "서울특별시 강남구", "서울특별시 마포구", "서울특별시 송파구", "부산광역시 해운대구",
    "부산광역시 부산진구", "대구광역시 수성구", "인천광역시 연수구", "광주광역시 북구",
    "대전광역시 유성구", "울산광역시 남구", "세종특별자치시", "경기도 수원시 영통구",
    "경기도 성남시 분당구", "경기도 고양시 일산동구", "경기도 양평군", "강원특별자치도 춘천시",
    "강원특별자치도 홍천군", "충청북도 청주시 흥덕구", "충청남도 천안시 서북구",
    "전북특별자치도 전주시 완산구", "전라남도 순천시", "경상북도 포항시 북구",
    "경상남도 창원시 성산구", "제주특별자치도 제주시", "제주특별자치도 서귀포시",
]
POSITIVE = [
    "[가상 리뷰] 발림성이 부드럽고 사용감이 만족스러워요.",
    "[가상 리뷰] 포장이 꼼꼼하고 배송이 빨라 재구매하고 싶어요.",
    "[가상 리뷰] 용량과 구성에 만족하며 편하게 사용하고 있어요.",
]
NEGATIVE = [
    "[가상 리뷰] 향이 제 취향과 달라 아쉬웠어요.",
    "[가상 리뷰] 배송이 예상보다 늦었고 포장 개선이 필요해요.",
    "[가상 리뷰] 제게는 사용감이 무거웠고 가격 대비 아쉬워요.",
]


def build_dummy_dataset(catalog: list[CatalogEntry]) -> DummySalesDataset:
    rng = Random(20261020)
    end = date(2026, 10, 20)
    start = date(2020, 1, 1)
    products = [row for row in catalog if row.sale_price is not None]
    if not products:
        raise ValueError("가격이 있는 공식 카탈로그가 필요합니다.")
    customers = [
        DummyCustomer(
            customer_id=f"dummy-customer-{i:04d}",
            gender="male" if i % 2 == 0 else "female",
            birth_year=end.year - (10 + (i // 2 % 8) * 10 + rng.randrange(10)),
            region=REGIONS[i % len(REGIONS)],
        )
        for i in range(2000)
    ]
    orders: list[DummyOrder] = []
    for i in range(2000):
        customer = customers[i if i < 1600 else i - 1600]
        # Recent activity plus complete synthetic historical coverage for moving averages.
        paid = (
            end - timedelta(days=i % 61)
            if i < 800 or i >= 1600
            else start + timedelta(days=rng.randrange((end - start).days + 1))
        )
        assert customer.birth_year is not None
        paid = max(paid, date(customer.birth_year + 10, 1, 1))
        count = 1 if i % 3 == 0 else rng.randint(2, 5)
        chosen = [products[i % len(products)]]
        chosen += rng.sample([row for row in products if row != chosen[0]], count - 1)
        items = []
        for j, product in enumerate(chosen):
            quantity = rng.choices([1, 2, 3, 5], [70, 20, 8, 2])[0]
            # Catalog prices are a test-fixture starting point only, frozen per item.
            price = product.sale_price
            assert price is not None
            variant = rng.choice(product.specifications) if product.specifications else None
            gross = price * quantity
            discount = gross * rng.choice([0, 0, 5, 10, 20]) // 100
            items.append(DummyItem(
                item_id=f"dummy-item-{i:04d}-{j}", product_id=product.product_id,
                quantity=quantity, unit_price=price, discount=discount,
                capacity=variant.capacity if variant else None,
                ean=variant.ean if variant else None,
            ))
        orders.append(DummyOrder(
            order_id=f"dummy-order-{i:04d}", customer_id=customer.customer_id,
            paid_on=paid, shipping=0 if sum(x.quantity*x.unit_price for x in items) >= 50000
            else 3000, items=items,
        ))
    refunds = []
    for i, order in enumerate(orders):
        if i % 10:
            continue
        item = order.items[0]
        full = i % 20 == 0
        quantity = item.quantity if full else 1
        amount = item.quantity * item.unit_price - item.discount
        refunds.append(DummyRefund(
            refund_id=f"dummy-refund-{i:04d}", order_id=order.order_id,
            item_id=item.item_id, completed_on=min(end, order.paid_on+timedelta(days=15)),
            quantity=quantity, amount=amount if full else amount // item.quantity,
            shipping_refund=order.shipping if full and len(order.items) == 1 else 0,
        ))
    reviews = []
    # Sample both genders and every age band, independent of the generated opinion.
    review_customers = rng.sample(customers[:1600], 400)
    by_customer: dict[str, list[DummyOrder]] = {}
    for order in orders:
        by_customer.setdefault(order.customer_id, []).append(order)
    for i, customer in enumerate(review_customers):
        order = rng.choice(by_customer[customer.customer_id])
        item = rng.choice(order.items)
        positive = i % 2 == 0
        reviews.append(DummyReview(
            review_id=f"dummy-review-{i:04d}", customer_id=customer.customer_id,
            order_id=order.order_id, item_id=item.item_id,
            created_on=min(end, order.paid_on+timedelta(days=rng.randint(1, 14))),
            rating=rng.choice([4, 5] if positive else [1, 2]),
            text=rng.choice(POSITIVE if positive else NEGATIVE),
        ))
    return DummySalesDataset(
        schema_version="1", synthetic=True, coverage_start=start, coverage_end=end,
        customers=customers, orders=orders, refunds=refunds, reviews=reviews,
    )
