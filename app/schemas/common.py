from decimal import Decimal
from typing import Annotated, Literal

from pydantic import PlainSerializer

TransactionType = Literal["Income", "Expense"]
PaymentMethod = Literal["UPI", "Cash", "Card", "Bank transfer"]

# DECIMAL(12,2) in the DB; serialised as a plain JSON number (what the frontend expects).
MoneyOut = Annotated[Decimal, PlainSerializer(lambda v: float(v), return_type=float, when_used="json")]
