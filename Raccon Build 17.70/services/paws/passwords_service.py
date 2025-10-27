# services/paws/passwords_service.py
import sqlite3
from .crypto_utils import encrypt_password, decrypt_password


class PasswordsService:
    def __init__(self, master_password: str, db_path: str):
        self.master_password = master_password
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _has_column(self, table: str, col: str) -> bool:
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        cols = {r[1] for r in cur.fetchall()}
        cur.close()
        return col in cols

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
        # добавить даты, если их нет
        if not self._has_column("passwords", "created_at"):
            cur.execute("ALTER TABLE passwords ADD COLUMN created_at TEXT DEFAULT (datetime('now'))")
        if not self._has_column("passwords", "updated_at"):
            cur.execute("ALTER TABLE passwords ADD COLUMN updated_at TEXT DEFAULT (datetime('now'))")
        self.conn.commit()
        cur.close()

    # --- CRUD ---
    def add_entry(self, service: str, username: str, password_plain: str, notes: str = "") -> int:
        enc = encrypt_password(self.master_password, password_plain)
        cur = self.conn.cursor()
        has_dates = self._has_column("passwords", "created_at") and self._has_column("passwords", "updated_at")

        if has_dates:
            cur.execute(
                "INSERT INTO passwords(service, username, password_enc, notes, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))",
                (service, username, enc, notes)
            )
        else:
            cur.execute(
                "INSERT INTO passwords(service, username, password_enc, notes) VALUES (?, ?, ?, ?)",
                (service, username, enc, notes)
            )
        self.conn.commit()
        new_id = cur.lastrowid
        cur.close()
        return new_id

    def update_entry(self, entry_id: int, service: str, username: str, password_plain: str | None, notes: str = ""):
        cur = self.conn.cursor()
        has_updated = self._has_column("passwords", "updated_at")

        if password_plain is None:
            if has_updated:
                cur.execute(
                    "UPDATE passwords SET service = ?, username = ?, notes = ?, updated_at = datetime('now') WHERE id = ?",
                    (service, username, notes, entry_id)
                )
            else:
                cur.execute(
                    "UPDATE passwords SET service = ?, username = ?, notes = ? WHERE id = ?",
                    (service, username, notes, entry_id)
                )
        else:
            enc = encrypt_password(self.master_password, password_plain)
            if has_updated:
                cur.execute(
                    "UPDATE passwords SET service = ?, username = ?, password_enc = ?, notes = ?, "
                    "updated_at = datetime('now') WHERE id = ?",
                    (service, username, enc, notes, entry_id)
                )
            else:
                cur.execute(
                    "UPDATE passwords SET service = ?, username = ?, password_enc = ?, notes = ? WHERE id = ?",
                    (service, username, enc, notes, entry_id)
                )

        self.conn.commit()
        cur.close()

    def get_entry_by_id(self, entry_id: int):
        has_created = self._has_column("passwords", "created_at")
        has_updated = self._has_column("passwords", "updated_at")
        cols = ["id", "service", "username", "password_enc", "notes"]
        if has_created:
            cols.append("created_at")
        if has_updated:
            cols.append("updated_at")

        cur = self.conn.cursor()
        cur.execute(f"SELECT {', '.join(cols)} FROM passwords WHERE id = ?", (entry_id,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return None

        d = dict(row)
        plain = decrypt_password(self.master_password, d["password_enc"])
        return {
            "id": d["id"],
            "service": d["service"],
            "username": d.get("username", ""),
            "password": plain,
            "notes": d.get("notes", ""),
            "created_at": d.get("created_at", ""),
            "updated_at": d.get("updated_at", "")
        }

    def list_entries(self, query: str | None = None, sort_by: str = "id", ascending: bool = True):
        allowed = {"id", "service", "username", "notes", "updated_at", "created_at"}
        sort_by = sort_by if sort_by in allowed else "id"
        order = "ASC" if ascending else "DESC"

        show_updated = self._has_column("passwords", "updated_at")
        sel_cols = ["id", "service", "username", "notes"]
        if show_updated:
            sel_cols.append("updated_at")

        cur = self.conn.cursor()
        if query:
            like = f"%{query}%"
            cur.execute(
                f"SELECT {', '.join(sel_cols)} FROM passwords "
                f"WHERE service LIKE ? OR username LIKE ? ORDER BY {sort_by} {order}",
                (like, like)
            )
        else:
            cur.execute(
                f"SELECT {', '.join(sel_cols)} FROM passwords ORDER BY {sort_by} {order}"
            )
        rows = cur.fetchall()
        cur.close()
        return rows

    def delete_entry(self, entry_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM passwords WHERE id = ?", (entry_id,))
        self.conn.commit()
        cur.close()
