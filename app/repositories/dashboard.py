from datetime import date
from decimal import Decimal

from pymysql.connections import Connection


def month_totals(db: Connection, user_id: int, start: date, end: date) -> dict:
    """Income / expense / count for [start, end)."""
    out = {"Income": Decimal(0), "Expense": Decimal(0), "count": 0}
    with db.cursor() as cur:
        cur.execute(
            """SELECT type, SUM(amount) AS total, COUNT(*) AS n
                 FROM transactions
                WHERE user_id = %s AND txn_date >= %s AND txn_date < %s
                GROUP BY type""",
            (user_id, start, end),
        )
        for r in cur.fetchall():
            out[r["type"]] = r["total"]
            out["count"] += r["n"]
    return out


def all_time_balance(db: Connection, user_id: int) -> Decimal:
    with db.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(CASE WHEN type = 'Income' THEN amount ELSE -amount END), 0) AS bal "
            "FROM transactions WHERE user_id = %s",
            (user_id,),
        )
        return cur.fetchone()["bal"]


def expense_by_category(db: Connection, user_id: int, start: date, end: date) -> list[dict]:
    with db.cursor() as cur:
        cur.execute(
            """SELECT c.id AS category_id, c.name, c.icon, SUM(t.amount) AS total
                 FROM transactions t
                 JOIN categories c ON c.id = t.category_id
                WHERE t.user_id = %s AND t.type = 'Expense'
                  AND t.txn_date >= %s AND t.txn_date < %s
                GROUP BY c.id, c.name, c.icon
                ORDER BY total DESC, c.name""",
            (user_id, start, end),
        )
        return cur.fetchall()


def monthly_cashflow(db: Connection, user_id: int, start: date, end: date) -> dict[tuple[str, str], Decimal]:
    """{('2026-11', 'Income'): total, ...} for [start, end); months with no data are absent."""
    with db.cursor() as cur:
        cur.execute(
            """SELECT DATE_FORMAT(txn_date, '%%Y-%%m') AS ym, type, SUM(amount) AS total
                 FROM transactions
                WHERE user_id = %s AND txn_date >= %s AND txn_date < %s
                GROUP BY ym, type""",
            (user_id, start, end),
        )
        return {(r["ym"], r["type"]): r["total"] for r in cur.fetchall()}
