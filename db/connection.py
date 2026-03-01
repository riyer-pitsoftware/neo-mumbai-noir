"""
Thread-safe SQLite connection manager with singleton pattern.
"""
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "neo_mumbai.db"


class ConnectionManager:
    """Thread-safe SQLite connection manager (one connection per thread)."""

    _local = threading.local()
    _initialized = threading.Lock()
    _schema_applied = False

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        conn = getattr(cls._local, "conn", None)
        if conn is None:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            cls._local.conn = conn
        return conn

    @classmethod
    @contextmanager
    def get_cursor(cls):
        """Yields a cursor inside a transaction. Auto-commits or rolls back."""
        conn = cls._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    @classmethod
    def execute(cls, sql: str, params=()) -> list:
        """Execute SQL and return all rows as sqlite3.Row objects."""
        with cls.get_cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    @classmethod
    def execute_many(cls, sql: str, params_list: list):
        """Execute SQL with many parameter sets."""
        with cls.get_cursor() as cur:
            cur.executemany(sql, params_list)

    @classmethod
    def execute_insert(cls, sql: str, params=()) -> int:
        """Execute an INSERT and return lastrowid."""
        with cls.get_cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid

    @classmethod
    def execute_script(cls, sql_script: str):
        """Execute a multi-statement SQL script."""
        conn = cls._get_connection()
        conn.executescript(sql_script)

    @classmethod
    def init_schema(cls):
        """Apply the schema if not already applied."""
        with cls._initialized:
            if cls._schema_applied:
                return
            schema_path = Path(__file__).resolve().parent / "migrations" / "v1_initial.sql"
            if schema_path.exists():
                cls.execute_script(schema_path.read_text())
            cls._schema_applied = True

    @classmethod
    def close(cls):
        """Close the current thread's connection."""
        conn = getattr(cls._local, "conn", None)
        if conn is not None:
            conn.close()
            cls._local.conn = None
