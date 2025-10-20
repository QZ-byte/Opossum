# services/db.py
import sqlite3
from typing import List, Tuple, Any, Optional

class Database:
    def __init__(self, path: str = "raccon.db"):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_pragmas()

    def _ensure_pragmas(self):
        try:
            cur = self.conn.cursor()
            cur.execute("PRAGMA foreign_keys = ON;")
            cur.close()
        except Exception:
            pass

    def execute(self, query: str, params: Tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        cur.close()

    def fetchall(self, query: str, params: Tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return [tuple(r) for r in rows]

    def fetchone(self, query: str, params: Tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()
        cur.close()
        return tuple(row) if row else None

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
