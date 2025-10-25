import sqlite3
from typing import Tuple, Iterable, Optional


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self.conn.commit()
        cur.close()

    def execute(self, sql: str, params: Tuple = ()) -> None:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        cur.close()

    def fetchall(self, sql: str, params: Tuple = ()) -> Iterable[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row

    def close(self):
        self.conn.close()
