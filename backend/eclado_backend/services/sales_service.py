from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from eclado_backend.services.product_insights_service import populate_insights
from eclado_shared.schemas.dashboard import SalesTotals
from eclado_shared.schemas.sales import (
    AmountBand,
    CohortTrend,
    CustomerCohort,
    DummySalesDataset,
    PeriodSales,
    Persona,
    ProductReviewSummary,
    RankedProduct,
    SalesAlert,
    SalesAnalysis,
    SalesPoint,
    Source,
)

AGE_BANDS = [f"{age}대" for age in range(10, 90, 10)] + ["10대 미만", "90대 이상", "미상"]
GENDERS = {"male": "남성", "female": "여성", "unknown": "미상"}


@dataclass(frozen=True)
class Event:
    day: date
    customer: str
    product: str
    order: str
    gender: str
    age_band: str
    gross: int = 0
    discount: int = 0
    paid: int = 0
    refund: int = 0
    units: int = 0
    payment: bool = False
    region: str = "미상"

    @property
    def net(self) -> int:
        return self.paid - self.refund


def age_band(birth_year: int | None, purchase_year: int) -> str:
    if birth_year is None:
        return "미상"
    age = purchase_year - birth_year
    return "10대 미만" if age < 10 else "90대 이상" if age >= 90 else f"{age // 10 * 10}대"


def events_for(data: DummySalesDataset) -> list[Event]:
    customers = {row.customer_id: row for row in data.customers}
    orders = {row.order_id: row for row in data.orders}
    result: list[Event] = []
    for order in data.orders:
        customer = customers[order.customer_id]
        for item in order.items:
            gross = item.quantity * item.unit_price
            result.append(
                Event(
                    order.paid_on,
                    order.customer_id,
                    item.product_id,
                    order.order_id,
                    customer.gender,
                    age_band(customer.birth_year, order.paid_on.year),
                    gross,
                    item.discount,
                    gross - item.discount,
                    0,
                    item.quantity,
                    True,
                    region=customer.region or "미상",
                )
            )
    for refund in data.refunds:
        order = orders[refund.order_id]
        customer = customers[order.customer_id]
        item = next(row for row in order.items if row.item_id == refund.item_id)
        result.append(
            Event(
                refund.completed_on,
                order.customer_id,
                item.product_id,
                order.order_id,
                customer.gender,
                age_band(customer.birth_year, order.paid_on.year),
                refund=refund.amount,
                units=-refund.quantity,
                region=customer.region or "미상",
            )
        )
    return result


def persona_customers(
    data: DummySalesDataset, start: date, end: date, persona: Persona
) -> set[str]:
    history = defaultdict(list)
    for order in data.orders:
        if order.paid_on <= end:
            history[order.customer_id].append(order)
    result = set()
    for customer, orders in history.items():
        first = min(order.paid_on for order in orders)
        amount = sum(
            item.quantity * item.unit_price - item.discount
            for order in orders
            for item in order.items
        )
        if (
            persona == "all"
            or persona == "new"
            and first >= start
            or persona == "returning"
            and first < start
            or persona == "repeat"
            and len(orders) >= 2
            or persona == "high_value"
            and amount / len(orders) >= 100000
            or persona == "discount"
            and any(item.discount > 0 for order in orders for item in order.items)
            or persona == "multi_item"
            and any(sum(item.quantity for item in order.items) >= 3 for order in orders)
        ):
            result.add(customer)
    return result


def amount_bands(values: list[float]) -> list[AmountBand]:
    limits = [30000, 50000, 100000, 200000]
    labels = ["3만원 미만", "3~5만원", "5~10만원", "10~20만원", "20만원 이상"]
    counts = [0] * len(labels)
    for value in values:
        index = next((index for index, limit in enumerate(limits) if value < limit), 4)
        counts[index] += 1
    return [
        AmountBand(label=label, count=count) for label, count in zip(labels, counts, strict=True)
    ]


def period_totals(
    points: list[SalesPoint], payments: list[Event], yearly: bool
) -> list[PeriodSales]:
    groups: dict[str, list[SalesPoint]] = defaultdict(list)
    for point in points:
        groups[str(point.day.year) if yearly else point.day.strftime("%Y-%m")].append(point)
    return [
        PeriodSales(
            period=key,
            net=sum(row.net for row in rows if row.net is not None)
            if any(row.net is not None for row in rows)
            else None,
            orders=len(
                {
                    row.order
                    for row in payments
                    if (str(row.day.year) if yearly else row.day.strftime("%Y-%m")) == key
                }
            ),
            complete=all(row.net is not None for row in rows),
        )
        for key, rows in groups.items()
    ]


class SalesAnalysisService:
    def __init__(self, product_names: dict[str, str]) -> None:
        self._names = product_names

    def analyze(
        self,
        data: DummySalesDataset | None,
        source: Source,
        start: date,
        end: date,
        gender: str = "all",
        age: str = "전체",
        persona: Persona = "all",
        alert_percent: float = 50,
        min_change: int = 100000,
    ) -> SalesAnalysis:
        result = SalesAnalysis(source=source, start=start, end=end, status="데이터 연동 대기")
        if data is None:
            result.status = (
                "더미 데이터 입력 대기" if source == "dummy" else "실제 데이터 연동 대기"
            )
            return result
        result.coverage_start, result.coverage_end = data.coverage_start, data.coverage_end
        result.complete = data.coverage_start <= start <= end <= data.coverage_end
        result.status = (
            "가상 데이터" if result.complete else "가상 데이터 · 조회 기간 일부 이력 없음"
        )
        eligible = persona_customers(data, start, end, persona)
        events = [
            row
            for row in events_for(data)
            if row.customer in eligible
            and (gender == "all" or row.gender == gender)
            and (age == "전체" or row.age_band == age)
        ]
        selected = [row for row in events if start <= row.day <= end]
        payments = [row for row in selected if row.payment]
        if end < data.coverage_start or start > data.coverage_end:
            result.notes.append("선택 기간에 제공된 이력이 없습니다. 0원으로 대체하지 않습니다.")
        else:
            order_ids = {row.order for row in payments}
            buyers = {row.customer for row in payments}
            shipping = sum(order.shipping for order in data.orders if order.order_id in order_ids)
            selected_orders = {row.order for row in selected}
            shipping -= sum(
                refund.shipping_refund
                for refund in data.refunds
                if start <= refund.completed_on <= end and refund.order_id in selected_orders
            )
            result.totals = SalesTotals(
                gross=sum(row.gross for row in selected),
                discounts=sum(row.discount for row in selected),
                refunds=sum(row.refund for row in selected),
                net=sum(row.net for row in selected),
                shipping=shipping,
                orders=len(order_ids),
                buyers=len(buyers),
            )
            result.paid_order_average = (
                sum(row.paid for row in payments) / len(order_ids) if order_ids else None
            )
            result.repeat_buyers = sum(
                len({row.order for row in payments if row.customer == buyer}) >= 2
                for buyer in buyers
            )
        by_day: dict[date, int] = defaultdict(int)
        for row in events:
            by_day[row.day] += row.net
        prefix = [0]
        history_days = (data.coverage_end - data.coverage_start).days + 1
        for offset in range(history_days):
            prefix.append(prefix[-1] + by_day[data.coverage_start + timedelta(days=offset)])

        def average(day: date, window: int) -> float | None:
            index = (day - data.coverage_start).days + 1
            if window <= index <= history_days:
                return (prefix[index] - prefix[index - window]) / window
            return None

        for offset in range((end - start).days + 1):
            day = start + timedelta(days=offset)
            result.daily.append(
                SalesPoint(
                    day=day,
                    net=by_day[day] if data.coverage_start <= day <= data.coverage_end else None,
                    ma20=average(day, 20),
                    ma30=average(day, 30),
                    ma365=average(day, 365),
                )
            )
        result.monthly = period_totals(result.daily, payments, False)
        result.yearly = period_totals(result.daily, payments, True)
        if data.coverage_start <= end <= data.coverage_end:
            result.day_net = by_day[end]
            month_start = end.replace(day=1)
            if month_start >= data.coverage_start:
                result.month_net = sum(
                    value for day, value in by_day.items() if month_start <= day <= end
                )
        previous_start = start - timedelta(days=(end - start).days + 1)
        if data.coverage_start <= previous_start and start - timedelta(days=1) <= data.coverage_end:
            result.previous_net = sum(
                value for day, value in by_day.items() if previous_start <= day < start
            )
        products: dict[str, list[Event]] = defaultdict(list)
        for row in selected:
            products[row.product].append(row)
        if result.totals is not None:
            result.products = sorted(
                [
                    RankedProduct(
                        product_id=key,
                        name=self._names[key],
                        net=sum(row.net for row in rows),
                        paid_amount=sum(row.paid for row in rows),
                        refunds=sum(row.refund for row in rows),
                        units=sum(row.units for row in rows),
                        orders=len({row.order for row in rows if row.payment}),
                    )
                    for key, rows in products.items()
                ],
                key=lambda row: (-row.net, row.product_id),
            )[:120]
            amounts: dict[str, int] = defaultdict(int)
            customer_orders: dict[str, set[str]] = defaultdict(set)
            for row in payments:
                amounts[row.order] += row.paid
                customer_orders[row.customer].add(row.order)
            result.order_amounts = amount_bands([float(value) for value in amounts.values()])
            result.customer_averages = amount_bands(
                [sum(amounts[key] for key in ids) / len(ids) for ids in customer_orders.values()]
            )
        result.alerts = self._alerts(events, data, end, alert_percent, min_change)
        result.age_cohorts = self._cohorts(selected, AGE_BANDS, "age_band")
        result.gender_cohorts = self._cohorts(selected, list(GENDERS), "gender")
        result.region_cohorts = self._cohorts(
            selected, sorted({row.region for row in selected}), "region"
        )
        review_orders = {order.order_id: order for order in data.orders}
        matching_items = {(row.order, row.product) for row in events if row.payment}
        reviews_by_product: dict[str, list[int]] = defaultdict(list)
        reviewers: set[str] = set()
        for review in data.reviews:
            order = review_orders[review.order_id]
            item = next(item for item in order.items if item.item_id == review.item_id)
            if (
                start <= review.created_on <= end
                and (order.order_id, item.product_id) in matching_items
            ):
                reviews_by_product[item.product_id].append(review.rating)
                reviewers.add(review.customer_id)
        result.product_reviews = [
            ProductReviewSummary(
                product_id=key, name=self._names[key], count=len(ratings),
                average_rating=round(sum(ratings) / len(ratings), 2) if ratings else None,
                positive=sum(value >= 4 for value in ratings),
                negative=sum(value <= 2 for value in ratings),
            )
            for key in sorted(set(products) | set(reviews_by_product))
            for ratings in [reviews_by_product[key]]
        ]
        result.review_count = sum(row.count for row in result.product_reviews)
        result.reviewer_count = len(reviewers)
        for month in result.monthly:
            rows = [row for row in selected if row.day.strftime("%Y-%m") == month.period]
            for cohort in self._cohorts(rows, AGE_BANDS, "age_band"):
                result.cohort_trends.append(
                    CohortTrend(period=month.period, label=cohort.label, net=cohort.net)
                )
            for cohort in self._cohorts(rows, list(GENDERS), "gender"):
                result.gender_trends.append(
                    CohortTrend(period=month.period, label=cohort.label, net=cohort.net)
                )
        result.notes += [
            "순상품매출=구매 시점 상품금액−할인−완료일 상품환불. 배송비·기타 매출 제외.",
            "평균 주문금액과 금액대 분포는 결제 시점 할인 후 상품금액 기준(배송비·환불 별도).",
            "연령은 구매연도−직접 제공 출생연도(연나이). 환불도 원구매 시점의 연령대로 연결.",
            "20/30/365일 이동평균은 완전한 달력 일수만 계산. 이전 이력 부족 시 선을 표시하지 않음.",
            "고객 세부 그룹은 기여 고객 5명 미만이면 금액 숨김. 성별·출생연도 미제공은 미상.",
            "고객 성향은 조회 종료일까지 제공된 구매 이력 기준이며 성향 간 중복 가능.",
        ]
        populate_insights(result, data, events, self._names)
        if (gender != "all" or age != "전체" or persona != "all") and len(
            {row.customer for row in selected}
        ) < 5:
            result.totals = None
            result.day_net = result.month_net = result.previous_net = None
            result.paid_order_average = None
            result.products, result.alerts = [], []
            result.order_amounts, result.customer_averages = [], []
            result.product_reviews = []
            result.review_count = result.reviewer_count = 0
            result.review_rises = []
            result.monthly_product_changes = result.monthly_age_changes = []
            result.daily = [SalesPoint(day=row.day, net=None) for row in result.daily]
            result.monthly = [row.model_copy(update={"net": None}) for row in result.monthly]
            result.yearly = [row.model_copy(update={"net": None}) for row in result.yearly]
            result.notes.append(
                "선택한 세부 고객군의 기여 고객이 5명 미만이므로 금액을 숨겼습니다."
            )
        return result

    def _cohorts(
        self, rows: list[Event], labels: list[str], attribute: str
    ) -> list[CustomerCohort]:
        result = []
        for label in labels:
            group = [row for row in rows if getattr(row, attribute) == label]
            buyers = len({row.customer for row in group})
            result.append(
                CustomerCohort(
                    label=GENDERS.get(label, label),
                    buyers=buyers,
                    net=sum(row.net for row in group) if buyers >= 5 else None,
                    suppressed=buyers < 5,
                )
            )
        return result

    def _alerts(
        self,
        events: list[Event],
        data: DummySalesDataset,
        end: date,
        percent_threshold: float,
        minimum: int,
    ) -> list[SalesAlert]:
        result: list[SalesAlert] = []
        daily: dict[str, dict[date, int]] = defaultdict(lambda: defaultdict(int))
        for event in events:
            daily[event.product][event.day] += event.net
        for window in (1, 7, 30):
            first = end - timedelta(days=window * 2 - 1)
            if first < data.coverage_start or end > data.coverage_end:
                continue
            candidates: list[SalesAlert] = []
            for key, values in daily.items():
                previous = sum(values[first + timedelta(days=offset)] for offset in range(window))
                current = sum(
                    values[first + timedelta(days=window + offset)] for offset in range(window)
                )
                delta = current - previous
                percent = 100 * delta / previous if previous > 0 else None
                if delta == 0 or abs(delta) < minimum:
                    continue
                if percent is not None and abs(percent) < percent_threshold:
                    continue
                candidates.append(
                    SalesAlert(
                        window=window,
                        direction="up" if delta > 0 else "down",
                        product_id=key,
                        name=self._names[key],
                        current=current,
                        previous=previous,
                        delta=delta,
                        percent=round(percent, 2) if percent is not None else None,
                        reason="직전 매출 0·음수로 증감률 계산 불가"
                        if percent is None
                        else "설정 임계값 초과",
                        series=[
                            SalesPoint(
                                day=first + timedelta(days=offset),
                                net=values[first + timedelta(days=offset)],
                            )
                            for offset in range(window * 2)
                        ],
                    )
                )
            for direction in ("up", "down"):
                result.extend(
                    sorted(
                        (row for row in candidates if row.direction == direction),
                        key=lambda row: (-abs(row.delta), row.product_id),
                    )[:5]
                )
        return result
