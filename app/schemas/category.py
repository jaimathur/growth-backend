from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from .common import TransactionType

CategoryName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class CategoryIn(BaseModel):
    name: CategoryName
    type: TransactionType
    icon: str = Field("📌", min_length=1, max_length=16)


class CategoryUpdate(BaseModel):
    """Type is intentionally not editable: it would invalidate existing transactions."""

    name: CategoryName | None = None
    icon: str | None = Field(None, min_length=1, max_length=16)


class CategoryOut(BaseModel):
    id: int
    name: str
    type: TransactionType
    icon: str
    is_system: bool
