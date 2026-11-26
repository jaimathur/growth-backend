"""MySQL access through PyMySQL (no ORM): a small connection pool + FastAPI dependency.

Transaction handling: connections run with autocommit OFF. Route handlers call
``conn.commit()`` explicitly after writes; anything not committed is rolled back
when the connection goes back to the pool (so an HTTPException never leaves
half-written data behind).
"""
import queue
import threading
from collections.abc import Iterator
from contextlib import contextmanager

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from .config import Settings, get_settings


def connect(settings: Settings, *, database: str | None = None, **extra) -> Connection:
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name if database is None else database,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        init_command="SET time_zone = '+00:00'",  # all DATETIMEs are UTC
        connect_timeout=10,
        **extra,
    )


class Pool:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._idle: queue.LifoQueue[Connection] = queue.LifoQueue()
        self._slots = threading.BoundedSemaphore(settings.db_pool_size)

    def acquire(self, timeout: float = 10.0) -> Connection:
        if not self._slots.acquire(timeout=timeout):
            raise RuntimeError("database connection pool exhausted")
        try:
            while True:
                try:
                    conn = self._idle.get_nowait()
                except queue.Empty:
                    return connect(self._settings)
                try:
                    conn.ping(reconnect=True)  # drop stale connections silently
                    return conn
                except pymysql.MySQLError:
                    self._close(conn)
        except BaseException:
            self._slots.release()
            raise

    def release(self, conn: Connection) -> None:
        try:
            conn.rollback()
            self._idle.put(conn)
        except pymysql.MySQLError:
            self._close(conn)
        finally:
            self._slots.release()

    def close_all(self) -> None:
        while True:
            try:
                self._close(self._idle.get_nowait())
            except queue.Empty:
                return

    @staticmethod
    def _close(conn: Connection) -> None:
        try:
            conn.close()
        except pymysql.MySQLError:
            pass


_pool: Pool | None = None
_pool_lock = threading.Lock()


def get_pool() -> Pool:
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = Pool(get_settings())
        return _pool


def close_pool() -> None:
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close_all()
            _pool = None


def get_db() -> Iterator[Connection]:
    """FastAPI dependency yielding a pooled connection."""
    pool = get_pool()
    conn = pool.acquire()
    try:
        yield conn
    finally:
        pool.release(conn)


@contextmanager
def db_connection() -> Iterator[Connection]:
    """Same as get_db, for scripts and tests."""
    gen = get_db()
    conn = next(gen)
    try:
        yield conn
    finally:
        gen.close()
