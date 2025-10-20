# services/notes_service.py
import datetime
from services.db import Database

class NotesService:
    def __init__(self, db: Database):
        self.db = db
        self._init_table()

    def _init_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            tags TEXT,
            created_at TEXT NOT NULL
        )
        """
        self.db.execute(query)

    def create_note(self, title: str, content: str = "", tags: str = ""):
        query = """
        INSERT INTO notes (title, content, tags, created_at)
        VALUES (?, ?, ?, ?)
        """
        created_at = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        self.db.execute(query, (title, content, tags, created_at))

    def get_all_notes(self):
        query = "SELECT id, title, tags, created_at FROM notes ORDER BY id DESC"
        return self.db.fetchall(query)

    def get_all_notes_full(self):
        query = "SELECT id, title, content, tags, created_at FROM notes ORDER BY id DESC"
        return self.db.fetchall(query)

    def get_note_by_id(self, note_id: int):
        query = "SELECT * FROM notes WHERE id = ?"
        return self.db.fetchone(query, (note_id,))

    def search_notes(self, keyword: str):
        query = """
        SELECT id, title, tags, created_at
        FROM notes
        WHERE title LIKE ? OR tags LIKE ?
        ORDER BY id DESC
        """
        like = f"%{keyword}%"
        return self.db.fetchall(query, (like, like))

    def update_note(self, note_id: int, title: str, content: str, tags: str):
        query = """
        UPDATE notes
        SET title = ?, content = ?, tags = ?
        WHERE id = ?
        """
        self.db.execute(query, (title, content, tags, note_id))

    def delete_note(self, note_id: int):
        query = "DELETE FROM notes WHERE id = ?"
        self.db.execute(query, (note_id,))
