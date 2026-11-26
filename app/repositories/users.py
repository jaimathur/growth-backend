from pymysql.connections import Connection

_COLS = "id, email, full_name, password_hash, role, is_active, created_at"


def get_by_id(db: Connection, user_id: int) -> dict | None:
    with db.cursor() as cur:
        cur.execute(f"SELECT {_COLS} FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


def get_by_email(db: Connection, email: str) -> dict | None:
    with db.cursor() as cur:
        cur.execute(f"SELECT {_COLS} FROM users WHERE email = %s", (email,))
        return cur.fetchone()


def create(db: Connection, *, email: str, full_name: str, password_hash: str) -> int:
    """Raises pymysql.err.IntegrityError (errno 1062) if the e-mail is taken."""
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, full_name, password_hash) VALUES (%s, %s, %s)",
            (email, full_name, password_hash),
        )
        return cur.lastrowid


def record_login(db: Connection, user_id: int, new_hash: str | None = None) -> None:
    with db.cursor() as cur:
        if new_hash:
            cur.execute(
                "UPDATE users SET last_login_at = UTC_TIMESTAMP(), password_hash = %s WHERE id = %s",
                (new_hash, user_id),
            )
        else:
            cur.execute("UPDATE users SET last_login_at = UTC_TIMESTAMP() WHERE id = %s", (user_id,))
