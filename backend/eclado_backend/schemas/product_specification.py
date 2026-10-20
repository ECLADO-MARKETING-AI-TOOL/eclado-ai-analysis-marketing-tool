from pydantic import BaseModel, Field


class SpecificationSourceRow(BaseModel):
    source_row: int
    english_name: str
    capacity: str
    ean: str | None = Field(default=None, pattern=r"^\d{13}$")


class ProductSpecificationMatch(BaseModel):
    catalog_name: str
    variants: list[SpecificationSourceRow] = Field(default_factory=list)
    note: str | None = None


class ProductSpecificationReference(BaseModel):
    source_file: str
    source_sha256: str
    source_sheet: str
    products: dict[str, ProductSpecificationMatch]
