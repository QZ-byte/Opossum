import tkinter as tk
from tkinter import ttk, messagebox


class NotesUI:
    def __init__(self, master, notes_service):
        self.master = master
        self.notes_service = notes_service

        self.frame = ttk.Frame(master)

        # Верхняя панель
        control = ttk.Frame(self.frame)
        control.pack(fill="x", padx=6, pady=6)

        ttk.Label(control, text="Заголовок:").pack(side="left")
        self.title_entry = ttk.Entry(control, width=30)
        self.title_entry.pack(side="left", padx=6)

        ttk.Label(control, text="Теги:").pack(side="left")
        self.tags_entry = ttk.Entry(control, width=20)
        self.tags_entry.pack(side="left", padx=6)

        ttk.Button(control, text="Добавить", command=self.add_note).pack(side="left", padx=6)

        ttk.Label(control, text="Поиск:").pack(side="left", padx=(20, 0))
        self.search_entry = ttk.Entry(control, width=25)
        self.search_entry.pack(side="left", padx=6)

        ttk.Button(control, text="Искать", command=self.search_notes).pack(side="left", padx=6)
        ttk.Button(control, text="Сброс", command=self.load_notes).pack(side="left", padx=6)

        # Таблица
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

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("title", width=320, anchor="w")
        self.tree.column("tags", width=160, anchor="w")
        self.tree.column("created_at", width=160, anchor="center")

        # Нижняя панель
        bottom = ttk.Frame(self.frame)
        bottom.pack(fill="x", padx=6, pady=6)

        ttk.Button(bottom, text="Удалить", command=self.delete_note).pack(side="left")
        ttk.Button(bottom, text="Просмотр", command=self.view_note).pack(side="left", padx=6)
        ttk.Button(bottom, text="Редактировать", command=self.edit_note).pack(side="left", padx=6)

        self.load_notes()

    # CRUD и поиск
    def load_notes(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = self.notes_service.get_all_notes()
            if rows:
                for note in rows:
                    self.tree.insert("", "end", values=note)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить заметки: {e}")

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
        q = self.search_entry.get().strip()
        if not q:
            self.load_notes()
            return
        try:
            results = self.notes_service.search_notes(q)
            for row in self.tree.get_children():
                self.tree.delete(row)
            for note in results:
                self.tree.insert("", "end", values=note)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def delete_note(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите заметку для удаления")
            return
        note_id = self.tree.item(sel[0])["values"][0]
        try:
            self.notes_service.delete_note(note_id)
            self.load_notes()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def view_note(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите заметку для просмотра")
            return
        note_id = self.tree.item(sel[0])["values"][0]
        try:
            note = self.notes_service.get_note_by_id(note_id)
            if note:
                _, title, content, tags, created_at = note
                messagebox.showinfo(
                    "Заметка",
                    f"Заголовок: {title}\nТеги: {tags}\nСоздано: {created_at}\n\n{content}"
                )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def edit_note(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите заметку для редактирования")
            return
        note_id = self.tree.item(sel[0])["values"][0]
        note = self.notes_service.get_note_by_id(note_id)
        if not note:
            return

        _, old_title, old_content, old_tags, _ = note

        win = tk.Toplevel(self.frame)
        win.title("Редактировать заметку")
        win.geometry("480x380")

        tk.Label(win, text="Заголовок:").pack(anchor="w", padx=8, pady=(8, 0))
        title_entry = tk.Entry(win, width=60)
        title_entry.insert(0, old_title)
        title_entry.pack(padx=8, pady=4)

        tk.Label(win, text="Теги:").pack(anchor="w", padx=8, pady=(8, 0))
        tags_entry = tk.Entry(win, width=60)
        tags_entry.insert(0, old_tags)
        tags_entry.pack(padx=8, pady=4)

        tk.Label(win, text="Содержимое:").pack(anchor="w", padx=8, pady=(8, 0))
        content_text = tk.Text(win, width=60, height=12)
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
                win.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        tk.Button(win, text="Сохранить", command=save_changes).pack(pady=10)
