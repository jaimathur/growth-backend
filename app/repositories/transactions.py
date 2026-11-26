from datetime import date

from pymysql.connections import Connection

_SELECT = """
    SELECT t.id, t.title, t.amount, t.type, t.payment_method, t.txn_date,
           t.created_at, t.updated_at,
           c.id AS category_id, c.name AS category_name, c.icon AS category_icon
    FROM transactions t
    JOIN categories c ON c.id = t.category_id
"""


def _row(r: dict) -> dict:
    return {
        "id": r["id"],
        "title": r["title"],
        "amount": r["amount"],
        "type": r["type"],
        "category": {"id": r["category_id"], "name": r["category_name"], "icon": r["category_icon"]},
        "payment_method": r["payment_method"],
        "date": r["txn_date"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    }


def _like_pattern(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def search(
    db: Connection,
    user_id: int,
    *,
    type_: str | None,
    category_id: int | None,
    q: str | None,
    date_from: date | None,
    date_to: date | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    # Every query is scoped by user_id first: this is the data-isolation guarantee.
    where = ["t.user_id = %s"]
    params: list = [user_id]
    if type_:
        where.append("t.type = %s")
        params.append(type_)
    if category_id:
        where.append("t.category_id = %s")
        params.append(category_id)
    if date_from:
        where.append("t.txn_date >= %s")
        params.append(date_from)
    if date_to:
        where.append("t.txn_date <= %s")
        params.append(date_to)
    if q:
        where.append("(t.title LIKE %s OR c.name LIKE %s)")
        pat = _like_pattern(q)
        params += [pat, pat]
    clause = " WHERE " + " AND ".join(where)  # fragments above are constants; values are bound params

    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM transactions t JOIN categories c ON c.id = t.category_id" + clause,
            params,
        )
        total = cur.fetchone()["n"]
        cur.execute(
            _SELECT + clause + " ORDER BY t.txn_date DESC, t.id DESC LIMIT %s OFFSET %s",
            params + [page_size, (page - 1) * page_size],
        )
        return [_row(r) for r in cur.fetchall()], total


def get(db: Connection, user_id: int, txn_id: int) -> dict | None:
    with db.cursor() as cur:
        cur.execute(_SELECT + " WHERE t.id = %s AND t.user_id = %s", (txn_id, user_id))
        r = cur.fetchone()
        return _row(r) if r else None


def create(db: Connection, user_id: int, d: dict) -> int:
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO transactions
                 (user_id, category_id, title, amount, type, payment_method, txn_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, d["category_id"], d["title"], d["amount"], d["type"], d["payment_method"], d["date"]),
        )
        return cur.lastrowid


def update(db: Connection, user_id: int, txn_id: int, d: dict) -> bool:
    with db.cursor() as cur:
        cur.execute(
            """UPDATE transactions
                  SET category_id = %s, title = %s, amount = %s, type = %s,
                      payment_method = %s, txn_date = %s
                WHERE id = %s AND user_id = %s""",
            (d["category_id"], d["title"], d["amount"], d["type"], d["payment_method"], d["date"],
             txn_id, user_id),
        )
        return cur.rowcount > 0


def delete(db: Connection, user_id: int, txn_id: int) -> bool:
    with db.cursor() as cur:
        cur.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (txn_id, user_id))
        return cur.rowcount > 0
