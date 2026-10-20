from datetime import datetime

from pydantic import BaseModel, Field

ORIGIN = "https://ecladomall.co.kr"


class PriceObservation(BaseModel):
    source_url: str
    observed_at: datetime
    sale_price: int | None
    discounted_price: int | None
    list_price: int | None


class CatalogProduct(BaseModel):
    product_id: str
    name: str
    url: str
    image_url: str | None = None
    categories: list[str] = Field(default_factory=list)
    observations: list[PriceObservation] = Field(default_factory=list)


class CatalogSnapshot(BaseModel):
    source: str = ORIGIN
    observed_at: datetime
    products: list[CatalogProduct] = Field(default_factory=list)
    visited_urls: list[str] = Field(default_factory=list)
    declared_counts: dict[str, int] = Field(default_factory=dict)
    collected_counts: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    complete: bool = False
    scope: str = "공개 홈 및 연결된 상품 분류 목록의 전체 페이지; 비공개·삭제·미노출 상품 제외"
