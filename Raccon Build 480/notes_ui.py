# notes_ui.py
import tkinter as tk
from tkinter import ttk, messagebox

class NotesUI:
    """
    UI для вкладки 'Заметки'.
    Использует переданный объект notes_service с методами:
      - create_note(title, content, tags)
      - get_all_notes()
      - get_all_notes_full()
      - get_note_by_id(id)
      - search_notes(keyword)
      - update_note(id, title, content, tags)
      - delete_note(id)
    """

    def __init__(self, master, notes_service):
        self.master = master
        self.notes_service = notes_service

        self.frame = ttk.Frame(master)

        # Верхняя панель управления
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill="x", padx=6, pady=6)

        ttk.Label(control_frame, text="Заголовок:").pack(side="left")
        self.title_entry = ttk.Entry(control_frame, width=30)
        self.title_entry.pack(side="left", padx=6)

        ttk.Label(control_frame, text="Теги:").pack(side="left")
        self.tags_entry = ttk.Entry(control_frame, width=20)
        self.tags_entry.pack(side="left", padx=6)

        add_btn = ttk.Button(control_frame, text="Добавить", command=self.add_note)
        add_btn.pack(side="left", padx=6)

        ttk.Label(control_frame, text="Поиск:").pack(side="left", padx=(20,0))
        self.search_entry = ttk.Entry(control_frame, width=25)
        self.search_entry.pack(side="left", padx=6)

        search_btn = ttk.Button(control_frame, text="Искать", command=self.search_notes)
        search_btn.pack(side="left", padx=6)

        reset_btn = ttk.Button(control_frame, text="Сброс", command=self.load_notes)
        reset_btn.pack(side="left", padx=6)

        # Таблица заметок
        self.tree = ttk.Treeview(
            self.frame,
            columns=("id", "title", "tags", "created_at"),
            show="headings",
            height=15
        )
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Заголовок")
        self.tree.heading("tags", text="Теги")
        self.tree.heading("created_at", text="Создано")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("title", width=320)
        self.tree.column("tags", width=160)
        self.tree.column("created_at", width=160)

        # Нижняя панель
        bottom_frame = ttk.Frame(self.frame)
        bottom_frame.pack(fill="x", padx=6, pady=6)

        delete_btn = ttk.Button(bottom_frame, text="Удалить", command=self.delete_note)
        delete_btn.pack(side="left")

        view_btn = ttk.Button(bottom_frame, text="Просмотр", command=self.view_note)
        view_btn.pack(side="left", padx=6)

        edit_btn = ttk.Button(bottom_frame, text="Редактировать", command=self.edit_note)
        edit_btn.pack(side="left", padx=6)

        # Инициализация данных
        self.load_notes()

    def load_notes(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = self.notes_service.get_all_notes()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить заметки: {e}")
            return
        if rows:
            for note in rows:
                self.tree.insert("", "end", values=note)

    def add_note(self):
        title = self.title_entry.get().strip()
        tags = self.tags_entry.get().strip()
        if not title:
            messagebox.showwarning("Ошибка", "Заголовок не может быть пустым")
            return
        try:
            self.notes_service.create_note(title, "", tags)
            self.title_entry.delete(0, "end")
            self.tags_entry.delete(0, "end")
            self.load_notes()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def search_notes(self):
        query = self.search_entry.get().strip()
        if not query:
            self.load_notes()
            return
        try:
            results = self.notes_service.search_notes(query)
            for row in self.tree.get_children():
                self.tree.delete(row)
            for note in results:
                self.tree.insert("", "end", values=note)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def delete_note(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите заметку для удаления")
            return
        try:
            note_id = self.tree.item(selected[0])["values"][0]
            self.notes_service.delete_note(note_id)
            self.load_notes()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def view_note(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите заметку для просмотра")
            return
        try:
            note_id = self.tree.item(selected[0])["values"][0]
            note = self.notes_service.get_note_by_id(note_id)
            if note:
                # формат записи: (id, title, content, tags, created_at) или sqlite Row
                if isinstance(note, tuple) and len(note) >= 5:
                    _, title, content, tags, created_at = note
                else:
                    # совместимость с sqlite3.Row
                    title = note["title"]
                    content = note.get("content", "")
                    tags = note.get("tags", "")
                    created_at = note.get("created_at", "")
                messagebox.showinfo(
                    "Заметка",
                    f"Заголовок: {title}\nТеги: {tags}\nСоздано: {created_at}\n\n{content}"
                )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def edit_note(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите заметку для редактирования")
            return
        try:
            note_id = self.tree.item(selected[0])["values"][0]
            note = self.notes_service.get_note_by_id(note_id)
            if not note:
                return

            if isinstance(note, tuple) and len(note) >= 5:
                _, old_title, old_content, old_tags, _ = note
            else:
                old_title = note.get("title", "")
                old_content = note.get("content", "")
                old_tags = note.get("tags", "")

            edit_win = tk.Toplevel(self.frame)
            edit_win.title("Редактировать заметку")
            edit_win.geometry("480x380")

            tk.Label(edit_win, text="Заголовок:").pack(anchor="w", padx=8, pady=(8,0))
            title_entry = tk.Entry(edit_win, width=60)
            title_entry.insert(0, old_title)
            title_entry.pack(padx=8, pady=4)

            tk.Label(edit_win, text="Теги:").pack(anchor="w", padx=8, pady=(8,0))
            tags_entry = tk.Entry(edit_win, width=60)
            tags_entry.insert(0, old_tags)
            tags_entry.pack(padx=8, pady=4)

            tk.Label(edit_win, text="Содержимое:").pack(anchor="w", padx=8, pady=(8,0))
            content_text = tk.Text(edit_win, width=60, height=12)
            content_text.insert("1.0", old_content)
            content_text.pack(padx=8, pady=4)

            def save_changes():
                new_title = title_entry.get().strip()
                new_tags = tags_entry.get().strip()
                new_content = content_text.get("1.0", "end").strip()
                if not new_title:
                    messagebox.showwarning("Ошибка", "Заголовок не может быть пустым")
                    return
                try:
                    self.notes_service.update_note(note_id, new_title, new_content, new_tags)
                    self.load_notes()
                    edit_win.destroy()
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))

            tk.Button(edit_win, text="Сохранить", command=save_changes).pack(pady=10)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
