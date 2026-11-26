from pymysql.connections import Connection

# A user sees every system category (user_id IS NULL) plus their own.
_SELECT = """
    SELECT id, name, type, icon, (user_id IS NULL) AS is_system
    FROM categories
"""


def _row(r: dict) -> dict:
    r["is_system"] = bool(r["is_system"])
    return r


def list_visible(db: Connection, user_id: int, type_: str | None = None) -> list[dict]:
    sql = _SELECT + " WHERE (user_id IS NULL OR user_id = %s)"
    params: list = [user_id]
    if type_:
        sql += " AND type = %s"
        params.append(type_)
    sql += " ORDER BY sort_order, name, id"
    with db.cursor() as cur:
        cur.execute(sql, params)
        return [_row(r) for r in cur.fetchall()]


def get_visible(db: Connection, user_id: int, category_id: int) -> dict | None:
    with db.cursor() as cur:
        cur.execute(
            _SELECT + " WHERE id = %s AND (user_id IS NULL OR user_id = %s)", (category_id, user_id)
        )
        r = cur.fetchone()
        return _row(r) if r else None


def get_owned(db: Connection, user_id: int, category_id: int) -> dict | None:
    with db.cursor() as cur:
        cur.execute(_SELECT + " WHERE id = %s AND user_id = %s", (category_id, user_id))
        r = cur.fetchone()
        return _row(r) if r else None


def create(db: Connection, user_id: int, name: str, type_: str, icon: str) -> int:
    """Raises IntegrityError (1062) on a duplicate name for this user and type."""
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO categories (user_id, name, type, icon) VALUES (%s, %s, %s, %s)",
            (user_id, name, type_, icon),
        )
        return cur.lastrowid


def update(db: Connection, user_id: int, category_id: int, fields: dict) -> None:
    allowed = {"name", "icon"}
    cols = [c for c in fields if c in allowed]
    if not cols:
        return
    assignments = ", ".join(f"{c} = %s" for c in cols)  # column names come from the whitelist above
    with db.cursor() as cur:
        cur.execute(
            f"UPDATE categories SET {assignments} WHERE id = %s AND user_id = %s",
            [fields[c] for c in cols] + [category_id, user_id],
        )


def delete(db: Connection, user_id: int, category_id: int) -> None:
    """Raises IntegrityError (1451) if transactions still reference the category."""
    with db.cursor() as cur:
        cur.execute("DELETE FROM categories WHERE id = %s AND user_id = %s", (category_id, user_id))
