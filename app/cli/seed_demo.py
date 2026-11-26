"""Create the demo user and load the sample transactions that used to live in the frontend.

    python -m app.cli.seed_demo            # create demo user + data (no-op if user exists)
    python -m app.cli.seed_demo --reset    # delete the demo user (cascades) and re-create it

Credentials: DEMO_EMAIL (default demo@pennywise.app) / DEMO_PASSWORD (default Demo@12345).
Development convenience only - do not run against production.
"""
import argparse
import os
from pathlib import Path

from pymysql.constants import CLIENT

from ..config import get_settings
from ..db import connect
from ..security import hash_password

SEED_FILE = Path(__file__).resolve().parents[2] / "seeds" / "demo_data.sql"


def run(reset: bool = False) -> bool:
    email = os.environ.get("DEMO_EMAIL", "demo@pennywise.app").lower()
    password = os.environ.get("DEMO_PASSWORD", "Demo@12345")
    conn = connect(get_settings(), client_flag=CLIENT.MULTI_STATEMENTS)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing = cur.fetchone()
            if existing and not reset:
                print(f"Demo user {email} already exists; nothing to do (use --reset to recreate).")
                return False
            if existing:
                cur.execute("DELETE FROM users WHERE id = %s", (existing["id"],))  # cascades
            cur.execute(
                "INSERT INTO users (email, full_name, password_hash) VALUES (%s, %s, %s)",
                (email, "Demo User", hash_password(password)),
            )
            cur.execute("SET @demo_user_id = %s", (cur.lastrowid,))
            cur.execute(SEED_FILE.read_text(encoding="utf-8"))
            while cur.nextset():
                pass
            cur.execute("SELECT COUNT(*) AS n FROM transactions WHERE user_id = @demo_user_id")
            n = cur.fetchone()["n"]
        conn.commit()
        print(f"Seeded demo user {email} with {n} transactions.")
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reset", action="store_true")
    run(reset=ap.parse_args().reset)
