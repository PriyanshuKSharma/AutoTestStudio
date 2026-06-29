import sqlite3
from config import DB_PATH

_conn: sqlite3.Connection = None


def get_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_schema()
    return _conn


def _init_schema():
    _conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity   TEXT NOT NULL,
            message    TEXT NOT NULL,
            signals    TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS can_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            can_id    TEXT NOT NULL,
            dlc       INTEGER NOT NULL,
            data      TEXT NOT NULL,
            channel   TEXT
        );
        CREATE TABLE IF NOT EXISTS test_results (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  TEXT NOT NULL,
            test_name  TEXT NOT NULL,
            status     TEXT NOT NULL,
            details    TEXT
        );
    """)
    _conn.commit()
