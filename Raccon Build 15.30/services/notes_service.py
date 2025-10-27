# services/notes_service.py
import json
import html
import os
from typing import List, Tuple, Optional
from datetime import datetime
from services.db import Database


class NotesService:
    def __init__(self, db: Database):
        self.db = db
        self._ensure_format_meta()

    def _ensure_format_meta(self):
        try:
            self.db.execute("ALTER TABLE notes ADD COLUMN format_meta TEXT NOT NULL DEFAULT '{}'")
        except Exception:
            pass

    def create_note(self, title: str, content: str = "", tags: str = "", format_meta: str = "{}") -> None:
        fm = self._normalize_format_meta(format_meta)
        self.db.execute(
            "INSERT INTO notes(title, content, tags, format_meta, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (title, content, tags, fm)
        )

    def get_all_notes(self) -> List[Tuple]:
        rows = self.db.fetchall("SELECT id, title, tags, created_at FROM notes ORDER BY id DESC")
        return [tuple(r) for r in rows] if rows else []

    def get_note_by_id(self, note_id: int) -> Optional[Tuple]:
        # Попробовать получить формат_meta вместе с остальными полями
        try:
            row = self.db.fetchone(
                "SELECT id, title, content, tags, created_at, COALESCE(format_meta, '{}') as format_meta FROM notes WHERE id = ?",
                (note_id,)
            )
            if row:
                return tuple(row)
            return None
        except Exception:
            # Если схема старая и column missing — вернуть 6-элементный кортеж с дефолтом
            row = self.db.fetchone(
                "SELECT id, title, content, tags, created_at FROM notes WHERE id = ?",
                (note_id,)
            )
            if row:
                vals = tuple(row)
                return (*vals, "{}")
            return None

    def search_notes(self, query: str) -> List[Tuple]:
        q = f"%{query}%"
        rows = self.db.fetchall(
            "SELECT id, title, tags, created_at FROM notes WHERE title LIKE ? OR tags LIKE ? ORDER BY id DESC",
            (q, q)
        )
        return [tuple(r) for r in rows] if rows else []

    def update_note(self, note_id: int, title: str, content: str, tags: str, format_meta: str = "{}") -> None:
        fm = self._normalize_format_meta(format_meta)
        self.db.execute(
            "UPDATE notes SET title = ?, content = ?, tags = ?, format_meta = ? WHERE id = ?",
            (title, content, tags, fm, note_id)
        )

    def delete_note(self, note_id: int) -> None:
        self.db.execute("DELETE FROM notes WHERE id = ?", (note_id,))

    def export_note_md(self, note_id: int, path: str) -> None:
        note = self.get_note_by_id(note_id)
        if not note:
            raise ValueError("Заметка не найдена")
        _id, title, content, tags, created_at, _ = note
        title_text = title or "(без заголовка)"
        lines = [
            f"# {title_text}",
            "",
            f"- ID: {_id}",
            f"- Создано: {created_at}",
            f"- Теги: {tags or ''}",
            "",
            content or ""
        ]
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def export_note_html(self, note_id: int, path: str) -> None:
        note = self.get_note_by_id(note_id)
        if not note:
            raise ValueError("Заметка не найдена")
        _id, title, content, tags, created_at, _ = note
        title_safe = html.escape(title or "(без заголовка)")
        content_safe = html.escape(content or "").replace("\n", "<br>\n")
        tags_safe = html.escape(tags or "")
        created_safe = html.escape(created_at or "")
        html_doc = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{title_safe}</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; max-width: 900px; margin: 2rem auto; color: #222; }}
.meta {{ color: #555; font-size: 0.9rem; margin-bottom: 0.8rem; }}
.content {{ margin-top: 1rem; line-height: 1.6; }}
hr {{ margin: 1rem 0; }}
</style>
</head>
<body>
<h1>{title_safe}</h1>
<div class="meta">
  <div><strong>ID:</strong> {_id}</div>
  <div><strong>Создано:</strong> {created_safe}</div>
  <div><strong>Теги:</strong> {tags_safe}</div>
</div>
<hr>
<div class="content">
  {content_safe}
</div>
</body>
</html>
"""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_doc)

    def _normalize_format_meta(self, fm) -> str:
        if fm is None:
            return "{}"
        if isinstance(fm, dict):
            try:
                return json.dumps(fm, ensure_ascii=False)
            except Exception:
                return "{}"
        if isinstance(fm, str):
            try:
                json.loads(fm)
                return fm
            except Exception:
                return "{}"
        return "{}"
