# services/notes_service.py
from datetime import datetime

class NotesService:
    def __init__(self, db):
        self.db = db
        self.init_table()

    def init_table(self):
        self.db.execute("""CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            created_at TEXT,
            tags TEXT,
            format_meta TEXT
        )""", commit=True)

    def add(self, title, content="", tags="", format_meta="{}"):
        self.db.execute(
            "INSERT INTO notes (title, content, created_at, tags, format_meta) VALUES (?, ?, ?, ?, ?)",
            (title, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tags, format_meta),
            commit=True
        )

    def list(self):
        return self.db.execute(
            "SELECT id, title, created_at, tags FROM notes ORDER BY created_at DESC",
            fetchall=True
        )

    def get(self, note_id):
        return self.db.execute(
            "SELECT id, title, content, tags, format_meta FROM notes WHERE id=?",
            (note_id,), fetchone=True
        )

    def update(self, note_id, title, content, tags, format_meta="{}"):
        self.db.execute(
            "UPDATE notes SET title=?, content=?, tags=?, format_meta=? WHERE id=?",
            (title, content, tags, format_meta, note_id),
            commit=True
        )

    def delete(self, note_id):
        self.db.execute("DELETE FROM notes WHERE id=?", (note_id,), commit=True)
