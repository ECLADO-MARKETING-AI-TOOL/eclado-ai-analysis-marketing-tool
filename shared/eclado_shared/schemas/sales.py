"""Sales preview transport and synthetic input contracts, without business rules."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from eclado_shared.schemas.dashboard import SalesTotals

Money = Annotated[int, Field(strict=True, ge=0)]
DummyId = Annotated[str, Field(pattern=r"^dummy-[A-Za-z0-9_-]{1,80}$")]
Source = Literal["pending", "demo", "dummy"]
Persona = Literal["all", "new", "returning", "repeat", "high_value", "discount", "multi_item"]


class DummyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DummyCustomer(DummyRecord):
    customer_id: DummyId
    gender: Literal["male", "female", "unknown"] = "unknown"
    birth_year: Annotated[int, Field(strict=True, ge=1900, le=2100)] | None = None
    region: Annotated[str, Field(max_length=80)] | None = None


class DummyItem(DummyRecord):
    item_id: DummyId
    product_id: Annotated[str, Field(pattern=r"^\d{1,12}$")]
    quantity: Annotated[int, Field(strict=True, ge=1, le=10000)]
    unit_price: Money
    discount: Money = 0
    capacity: Annotated[str, Field(max_length=80)] | None = None
    ean: Annotated[str, Field(pattern=r"^\d{8,14}$")] | None = None


class DummyOrder(DummyRecord):
    order_id: DummyId
    customer_id: DummyId
    paid_on: date
    shipping: Money = 0
    items: list[DummyItem] = Field(min_length=1, max_length=20)


class DummyRefund(DummyRecord):
    refund_id: DummyId
    order_id: DummyId
    item_id: DummyId
    completed_on: date
    quantity: Annotated[int, Field(strict=True, ge=0)] = 0
    amount: Money
    shipping_refund: Money = 0


class DummyReview(DummyRecord):
    review_id: DummyId
    customer_id: DummyId
    order_id: DummyId
    item_id: DummyId
    created_on: date
    rating: Annotated[int, Field(strict=True, ge=1, le=5)]
    text: Annotated[str, Field(min_length=1, max_length=500)]


class DummySalesDataset(DummyRecord):
    schema_version: Literal["1"]
    synthetic: Literal[True]
    coverage_start: date
    coverage_end: date
    customers: list[DummyCustomer] = Field(max_length=10000)
    orders: list[DummyOrder] = Field(max_length=10000)
    refunds: list[DummyRefund] = Field(default_factory=list, max_length=20000)
    reviews: list[DummyReview] = Field(default_factory=list, max_length=20000)
    product_launch_dates: dict[str, date] = Field(default_factory=dict)


class DummyImportResult(BaseModel):
    status: Literal["imported", "unchanged"]
    customers: int
    orders: int
    items: int
    dataset_hash: str
    reviews: int = 0


class SalesPoint(BaseModel):
    day: date
    net: int | None
    ma20: float | None = None
    ma30: float | None = None
    ma365: float | None = None


class PeriodSales(BaseModel):
    period: str
    net: int | None
    orders: int = 0
    complete: bool = False


class RankedProduct(BaseModel):
    product_id: str
    name: str
    net: int
    paid_amount: int
    refunds: int
    units: int
    orders: int


class AmountBand(BaseModel):
    label: str
    count: int


class SalesAlert(BaseModel):
    window: Literal[1, 7, 30]
    direction: Literal["up", "down"]
    product_id: str
    name: str
    current: int
    previous: int
    delta: int
    percent: float | None
    reason: str
    series: list[SalesPoint]


class CustomerCohort(BaseModel):
    label: str
    buyers: int
    net: int | None
    suppressed: bool


class CohortTrend(BaseModel):
    period: str
    label: str
    net: int | None


class ProductReviewSummary(BaseModel):
    product_id: str
    name: str
    count: int
    average_rating: float | None
    positive: int
    negative: int


class ReviewRise(BaseModel):
    product_id: str
    name: str
    current: int
    previous: int
    delta: int
    percent: float | None


class MonthlyChange(BaseModel):
    label: str
    product_id: str | None = None
    previous: int
    current: int
    previous_average: float
    current_average: float
    delta: int
    percent: float
    previous_units: int
    current_units: int
    units_delta: int
    units_percent: float | None
    launch_status: Literal["established", "new", "unknown"] = "established"


class SalesAnalysis(BaseModel):
    source: Source
    start: date
    end: date
    status: str
    coverage_start: date | None = None
    coverage_end: date | None = None
    complete: bool = False
    totals: SalesTotals | None = None
    day_net: int | None = None
    month_net: int | None = None
    previous_net: int | None = None
    paid_order_average: float | None = None
    repeat_buyers: int = 0
    daily: list[SalesPoint] = Field(default_factory=list)
    monthly: list[PeriodSales] = Field(default_factory=list)
    yearly: list[PeriodSales] = Field(default_factory=list)
    products: list[RankedProduct] = Field(default_factory=list)
    order_amounts: list[AmountBand] = Field(default_factory=list)
    customer_averages: list[AmountBand] = Field(default_factory=list)
    alerts: list[SalesAlert] = Field(default_factory=list)
    age_cohorts: list[CustomerCohort] = Field(default_factory=list)
    gender_cohorts: list[CustomerCohort] = Field(default_factory=list)
    region_cohorts: list[CustomerCohort] = Field(default_factory=list)
    product_reviews: list[ProductReviewSummary] = Field(default_factory=list)
    review_count: int = 0
    reviewer_count: int = 0
    review_rises: list[ReviewRise] = Field(default_factory=list)
    monthly_product_changes: list[MonthlyChange] = Field(default_factory=list)
    monthly_age_changes: list[MonthlyChange] = Field(default_factory=list)
    change_history_complete: bool = False
    cohort_trends: list[CohortTrend] = Field(default_factory=list)
    gender_trends: list[CohortTrend] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
