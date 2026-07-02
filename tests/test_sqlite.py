import os
import sqlite3

from database.sqlite import get_db


def test_get_db_creates_and_returns_connection():
    if os.path.exists("autoteststudio.db"):
        os.remove("autoteststudio.db")

    conn = get_db()

    assert isinstance(conn, sqlite3.Connection)
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"events", "can_log", "test_results"}.issubset(tables)
