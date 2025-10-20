from typing import List, Tuple, Optional
from services.db import Database


class NotesService:
    def __init__(self, db: Database):
        self.db = db

    # Create
    def create_note(self, title: str, content: str, tags: str) -> None:
        self.db.execute(
            "INSERT INTO notes(title, content, tags) VALUES (?, ?, ?)",
            (title, content, tags)
        )

    # Read
    def get_all_notes(self) -> List[Tuple]:
        rows = self.db.fetchall(
            "SELECT id, title, tags, created_at FROM notes ORDER BY id DESC"
        )
        return [tuple(r) for r in rows]

    def get_note_by_id(self, note_id: int) -> Optional[Tuple]:
        row = self.db.fetchone(
            "SELECT id, title, content, tags, created_at FROM notes WHERE id = ?",
            (note_id,)
        )
        return tuple(row) if row else None

    def search_notes(self, query: str) -> List[Tuple]:
        q = f"%{query}%"
        rows = self.db.fetchall(
            "SELECT id, title, tags, created_at FROM notes WHERE title LIKE ? OR tags LIKE ? ORDER BY id DESC",
            (q, q)
        )
        return [tuple(r) for r in rows]

    # Update
    def update_note(self, note_id: int, title: str, content: str, tags: str) -> None:
        self.db.execute(
            "UPDATE notes SET title = ?, content = ?, tags = ? WHERE id = ?",
            (title, content, tags, note_id)
        )

    # Delete
    def delete_note(self, note_id: int) -> None:
        self.db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
