import datetime as dt
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from .common import MoneyOut, PaymentMethod, TransactionType

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=70)]
# DECIMAL(12,2): at most 10 integer digits, 2 decimals
AmountIn = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class TransactionIn(BaseModel):
    title: Title
    amount: AmountIn
    type: TransactionType
    category_id: int = Field(gt=0)
    payment_method: PaymentMethod
    date: dt.date


class TransactionPatch(BaseModel):
    """Partial update: only fields present in the request body are changed."""

    title: Title | None = None
    amount: AmountIn | None = None
    type: TransactionType | None = None
    category_id: int | None = Field(None, gt=0)
    payment_method: PaymentMethod | None = None
    date: dt.date | None = None


class CategoryRef(BaseModel):
    id: int
    name: str
    icon: str


class TransactionOut(BaseModel):
    id: int
    title: str
    amount: MoneyOut
    type: TransactionType
    category: CategoryRef
    payment_method: PaymentMethod
    date: dt.date
    created_at: dt.datetime
    updated_at: dt.datetime


class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int
