import sqlite3
from pathlib import Path
from .crypto_utils import encrypt_password, decrypt_password

DB_PATH = Path("paws.db")


class PasswordsService:
    def __init__(self, master_password: str):
        self.master_password = master_password
        self.conn = sqlite3.connect(DB_PATH)
        self._init_db()

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            username TEXT,
            password_enc TEXT NOT NULL,
            notes TEXT
        )
        """)
        self.conn.commit()

    # --- CRUD ---
    def add_entry(self, service: str, username: str, password_plain: str, notes: str = ""):
        enc = encrypt_password(self.master_password, password_plain)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO passwords(service, username, password_enc, notes) VALUES (?, ?, ?, ?)",
            (service, username, enc, notes)
        )
        self.conn.commit()

    def get_entry(self, service: str):
        """Получить запись по имени сервиса"""
        cur = self.conn.cursor()
        cur.execute("SELECT id, service, username, password_enc, notes FROM passwords WHERE service=?", (service,))
        row = cur.fetchone()
        if not row:
            return None
        pid, service, username, enc, notes = row
        plain = decrypt_password(self.master_password, enc)
        return {"id": pid, "service": service, "username": username, "password": plain, "notes": notes}

    def get_entry_by_id(self, entry_id: int):
        """Получить запись по ID (для UI)"""
        cur = self.conn.cursor()
        cur.execute("SELECT id, service, username, password_enc, notes FROM passwords WHERE id=?", (entry_id,))
        row = cur.fetchone()
        if not row:
            return None
        pid, service, username, enc, notes = row
        plain = decrypt_password(self.master_password, enc)
        return {"id": pid, "service": service, "username": username, "password": plain, "notes": notes}

    def list_entries(self):
        """Список всех записей (без паролей, только мета)"""
        cur = self.conn.cursor()
        cur.execute("SELECT id, service, username, notes FROM passwords")
        return cur.fetchall()

    def delete_entry(self, entry_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM passwords WHERE id=?", (entry_id,))
        self.conn.commit()
