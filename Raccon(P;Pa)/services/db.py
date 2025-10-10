# services/db.py
import sqlite3

class Database:
    def __init__(self, db_name="raccon.db"):
        self.db_name = db_name

    def execute(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute(query, params)
        result = None
        if fetchone:
            result = cur.fetchone()
        elif fetchall:
            result = cur.fetchall()
        if commit:
            conn.commit()
        conn.close()
        return result
