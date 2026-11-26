"""Apply SQL migrations from backend/migrations in version order.

    python -m app.cli.migrate            # apply pending migrations
    python -m app.cli.migrate --status   # list applied / pending

Files are named V<number>__<description>.sql. Applied migrations are recorded in
`schema_migrations` with a checksum; editing an applied file is refused (add a new
migration instead). A MySQL advisory lock stops two runners racing.
Note: MySQL DDL auto-commits, so a failing migration can't be rolled back automatically;
keep each migration small and focused.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

from pymysql.constants import CLIENT

from ..config import get_settings
from ..db import connect

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
_NAME = re.compile(r"^V(\d+)__(.+)\.sql$")

_BOOKKEEPING = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version     INT UNSIGNED NOT NULL,
  name        VARCHAR(255) NOT NULL,
  checksum    CHAR(64)     NOT NULL,
  applied_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def discover(directory: Path = MIGRATIONS_DIR) -> list[tuple[int, str, Path]]:
    found = []
    for f in directory.glob("*.sql"):
        m = _NAME.match(f.name)
        if not m:
            raise SystemExit(f"Bad migration file name: {f.name} (expected V<number>__<name>.sql)")
        found.append((int(m.group(1)), f.name, f))
    found.sort()
    versions = [v for v, _, _ in found]
    if len(versions) != len(set(versions)):
        raise SystemExit("Duplicate migration version numbers")
    return found


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(status_only: bool = False, directory: Path = MIGRATIONS_DIR) -> int:
    conn = connect(get_settings(), client_flag=CLIENT.MULTI_STATEMENTS)
    applied_now = 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT GET_LOCK('pennywise_migrate', 30) AS got")
            if not cur.fetchone()["got"]:
                raise SystemExit("Could not obtain migration lock")
            cur.execute(_BOOKKEEPING)
            cur.execute("SELECT version, name, checksum FROM schema_migrations")
            applied = {r["version"]: r for r in cur.fetchall()}

            for version, name, path in discover(directory):
                done = applied.get(version)
                if done:
                    if done["checksum"] != _checksum(path):
                        raise SystemExit(f"{name} was modified after being applied (checksum mismatch)")
                    print(f"  applied  {name}")
                    continue
                if status_only:
                    print(f"  PENDING  {name}")
                    continue
                print(f"  applying {name} ...", end=" ", flush=True)
                cur.execute(path.read_text(encoding="utf-8"))
                while cur.nextset():  # drain results so errors in later statements surface
                    pass
                cur.execute(
                    "INSERT INTO schema_migrations (version, name, checksum) VALUES (%s, %s, %s)",
                    (version, name, _checksum(path)),
                )
                conn.commit()
                applied_now += 1
                print("ok")
            cur.execute("SELECT RELEASE_LOCK('pennywise_migrate')")
    finally:
        conn.close()
    return applied_now


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", action="store_true", help="only show migration status")
    args = ap.parse_args()
    n = run(status_only=args.status)
    if not args.status:
        print(f"Done. {n} migration(s) applied.")


if __name__ == "__main__":
    sys.exit(main())
