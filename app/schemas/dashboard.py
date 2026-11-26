from pydantic import BaseModel

from .common import MoneyOut


class CategoryTotal(BaseModel):
    category_id: int
    name: str
    icon: str
    total: MoneyOut
    percentage: float  # share of the month's expenses, 0-100


class DashboardSummary(BaseModel):
    month: str  # YYYY-MM
    income: MoneyOut
    expense: MoneyOut
    balance: MoneyOut  # income - expense for the month
    savings_rate: float  # balance / income * 100, 0 when there is no income
    all_time_balance: MoneyOut
    transaction_count: int
    top_expense_category: CategoryTotal | None
    expense_by_category: list[CategoryTotal]


class CashflowPoint(BaseModel):
    month: str  # YYYY-MM
    income: MoneyOut
    expense: MoneyOut


class Cashflow(BaseModel):
    months: list[CashflowPoint]
