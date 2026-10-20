from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class SalesTotals(BaseModel):
    gross: int = 0
    discounts: int = 0
    refunds: int = 0
    net: int = 0
    shipping: int = 0
    orders: int = 0
    buyers: int = 0
    other_revenue: int | None = None


class DailySales(BaseModel):
    day: date
    net: int
    refunds: int


class ProductPerformance(BaseModel):
    product_id: str
    name: str
    units: int
    net: int
    review_count: int
    average_rating: float | None


class CustomerOverview(BaseModel):
    buyers: int = 0
    first_time_buyers: int = 0
    returning_buyers: int = 0
    repeat_order_buyers: int = 0


class PurchaseRow(BaseModel):
    order_id: str
    paid_on: date
    product: str
    quantity: int
    amount: int


class Recommendation(BaseModel):
    title: str
    evidence: str
    action: str
    measurement: str


class ProductSpecification(BaseModel):
    capacity: str
    ean: str | None
    source_name: str
    source_row: int


class CatalogEntry(BaseModel):
    product_id: str
    name: str
    specifications: list[ProductSpecification] = Field(default_factory=list)
    specification_note: str | None = None
    url: str
    sale_price: int | None
    discounted_price: int | None
    list_price: int | None
    price_source: str
    observed_at: datetime
    price_conflict: bool


class DashboardResponse(BaseModel):
    source: Literal["demo", "pending"]
    status: str
    start: date
    end: date
    metric_policy: str
    catalog: list[CatalogEntry] = Field(default_factory=list)
    catalog_status: str = "카탈로그 미연결"
    catalog_observed_at: datetime | None = None
    specification_source: str | None = None
    totals: SalesTotals | None = None
    daily: list[DailySales] = Field(default_factory=list)
    products: list[ProductPerformance] = Field(default_factory=list)
    customers: CustomerOverview | None = None
    purchases: list[PurchaseRow] = Field(default_factory=list)
    summary: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
