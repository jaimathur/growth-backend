from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Query

from ...deps import DB, CurrentUser
from ...repositories import dashboard as repo
from ...schemas.dashboard import CashflowPoint, Cashflow, CategoryTotal, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

MONTH_RE = r"^\d{4}-(0[1-9]|1[0-2])$"


def _first_of(month: str | None) -> date:
    if month:
        y, m = month.split("-")
        return date(int(y), int(m), 1)
    t = date.today()
    return date(t.year, t.month, 1)


def _add_months(d: date, n: int) -> date:
    idx = d.year * 12 + (d.month - 1) + n
    return date(idx // 12, idx % 12 + 1, 1)


@router.get("/summary", response_model=DashboardSummary)
def summary(
    db: DB,
    user: CurrentUser,
    month: str | None = Query(None, pattern=MONTH_RE, description="YYYY-MM, defaults to the current month"),
):
    start = _first_of(month)
    end = _add_months(start, 1)
    t = repo.month_totals(db, user["id"], start, end)
    income, expense = t["Income"], t["Expense"]
    balance = income - expense
    cats = repo.expense_by_category(db, user["id"], start, end)
    by_cat = [
        CategoryTotal(
            **c, percentage=float(round(c["total"] / expense * 100, 1)) if expense else 0.0
        )
        for c in cats
    ]
    return DashboardSummary(
        month=start.strftime("%Y-%m"),
        income=income,
        expense=expense,
        balance=balance,
        savings_rate=float(round(balance / income * 100, 1)) if income else 0.0,
        all_time_balance=repo.all_time_balance(db, user["id"]),
        transaction_count=t["count"],
        top_expense_category=by_cat[0] if by_cat else None,
        expense_by_category=by_cat,
    )


@router.get("/cashflow", response_model=Cashflow)
def cashflow(
    db: DB,
    user: CurrentUser,
    months: int = Query(6, ge=1, le=24, description="How many months to return"),
    end_month: str | None = Query(None, pattern=MONTH_RE, description="Last month included; defaults to current"),
):
    last = _first_of(end_month)
    first = _add_months(last, -(months - 1))
    data = repo.monthly_cashflow(db, user["id"], first, _add_months(last, 1))
    points = []
    for i in range(months):  # zero-fill so the chart always gets a continuous series
        key = _add_months(first, i).strftime("%Y-%m")
        points.append(
            CashflowPoint(
                month=key,
                income=data.get((key, "Income"), Decimal(0)),
                expense=data.get((key, "Expense"), Decimal(0)),
            )
        )
    return Cashflow(months=points)
