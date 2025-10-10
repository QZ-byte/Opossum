# notes_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "notes_settings.json")


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"ask_delete_confirm": True}


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f)
    except Exception:
        pass


def confirm_delete_dialog(parent, title="Подтверждение", message="Удалить заметку?", default_dont_ask=False):
    win = tk.Toplevel(parent)
    win.title(title)
    win.resizable(False, False)

    WIDTH, HEIGHT = 320, 150
    win.geometry(f"{WIDTH}x{HEIGHT}")

    win.transient(parent)
    win.grab_set()

    try:
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - WIDTH) // 2
        y = py + (ph - HEIGHT) // 2
        win.geometry(f"+{max(x,0)}+{max(y,0)}")
    except Exception:
        pass

    confirmed = {"value": False}
    dont_ask_var = tk.BooleanVar(value=bool(default_dont_ask))

    frm = ttk.Frame(win, padding=(12, 10, 12, 10))
    frm.pack(fill="both", expand=True)

    msg = ttk.Label(frm, text=message, wraplength=WIDTH - 40, anchor="center", justify="center")
    msg.pack(pady=(4, 8), fill="x")

    chk = ttk.Checkbutton(frm, text="Больше не спрашивать", variable=dont_ask_var)
    chk.pack(pady=(0, 8))

    sep = ttk.Separator(frm, orient="horizontal")
    sep.pack(fill="x", pady=(0, 8))

    btn_frame = ttk.Frame(frm)
    btn_frame.pack(fill="x")

    def on_confirm():
        confirmed["value"] = True
        win.destroy()

    def on_cancel():
        win.destroy()

    left_frame = ttk.Frame(btn_frame)
    left_frame.pack(side="left", fill="x", expand=True)
    right_frame = ttk.Frame(btn_frame)
    right_frame.pack(side="right")

    yes_btn = ttk.Button(left_frame, text="Да", command=on_confirm)
    yes_btn.pack(side="left", padx=(0, 6))
    no_btn = ttk.Button(right_frame, text="Нет", command=on_cancel)
    no_btn.pack(side="right")

    win.bind("<Return>", lambda e: on_confirm())
    win.bind("<Escape>", lambda e: on_cancel())

    yes_btn.focus_set()

    parent.wait_window(win)
    return confirmed["value"], bool(dont_ask_var.get())


class NotesUI:
    def __init__(self, parent, notes_service, settings=None):
        self.service = notes_service
        self.frame = ttk.Frame(parent)

        # settings: общий словарь, передаваемый по ссылке
        self.settings = settings if settings is not None else load_settings()
        self.ask_delete_confirm = bool(self.settings.get("ask_delete_confirm", True))

        # --- верхняя панель: добавление + поиск ---
        top = ttk.Frame(self.frame)
        top.pack(fill="x", pady=5, padx=5)

        # добавление
        add_frame = ttk.Frame(top)
        add_frame.pack(side="left", fill="x", expand=False)

        ttk.Label(add_frame, text="Заголовок:").pack(side="left")
        self.title_entry = ttk.Entry(add_frame, width=30)
        self.title_entry.pack(side="left", padx=5)

        ttk.Label(add_frame, text="Теги:").pack(side="left")
        self.tags_entry = ttk.Entry(add_frame, width=20)
        self.tags_entry.pack(side="left", padx=5)

        add_btn = ttk.Button(add_frame, text="Добавить", command=self.add_note)
        add_btn.pack(side="left", padx=5)

        # поиск
        search_frame = ttk.Frame(top)
        search_frame.pack(side="right", fill="x", expand=True)

        ttk.Label(search_frame, text="Поиск:").pack(side="left", padx=(0,6))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True)
        # триггер на изменение: фильтрация в реальном времени
        self.search_var.trace_add("write", lambda *a: self.refresh_notes())

        # --- таблица заметок ---
        self.tree = ttk.Treeview(
            self.frame,
            columns=("id", "title", "created", "tags"),
            show="headings",
            selectmode="browse"
        )
        self.tree.heading("id", text="ID", command=lambda: self.sort_by("id"))
        self.tree.heading("title", text="Заголовок", command=lambda: self.sort_by("title"))
        self.tree.heading("created", text="Создано", command=lambda: self.sort_by("created"))
        self.tree.heading("tags", text="Теги", command=lambda: self.sort_by("tags"))

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("title", width=320, anchor="w")
        self.tree.column("created", width=150, anchor="center")
        self.tree.column("tags", width=120, anchor="w")

        self.tree.pack(fill="both", expand=True, pady=10, padx=5)

        # events
        self.tree.bind("<Double-1>", self.open_edit_window)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Button-2>", self.show_context_menu)

        # context menu
        self.menu = tk.Menu(self.frame, tearoff=0)
        self.menu.add_command(label="Открыть", command=self.open_selected_note)
        self.menu.add_command(label="Переименовать", command=self.rename_note)
        self.menu.add_command(label="Удалить", command=self.delete_note)

        # sorting default
        self.sort_column = "created"
        self.sort_reverse = True

        # хоткеи (локально в рамках приложения)
        # Ctrl+N — фокус в поле заголовка (быстро начать новую заметку)
        # Ctrl+F — фокус в поиск
        self.frame.bind_all("<Control-n>", lambda e: self.title_entry.focus_set())
        self.frame.bind_all("<Control-N>", lambda e: self.title_entry.focus_set())
        self.frame.bind_all("<Control-f>", lambda e: self.search_entry.focus_set())
        self.frame.bind_all("<Control-F>", lambda e: self.search_entry.focus_set())

        self.refresh_notes()

    def add_note(self):
        title = self.title_entry.get().strip()
        tags = self.tags_entry.get().strip()
        if not title:
            messagebox.showwarning("Ошибка", "Заголовок не может быть пустым")
            return
        try:
            self.service.add(title, "", tags)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить заметку: {e}")
            return
        self.title_entry.delete(0, tk.END)
        self.tags_entry.delete(0, tk.END)
        # если есть активный поиск, обновляем - новая заметка может не попасть в фильтр
        self.refresh_notes()

    def refresh_notes(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        notes = self.service.list() or []
        query = (self.search_var.get() or "").strip().lower()
        if query:
            filtered = []
            for n in notes:
                title = (n[1] if len(n) > 1 and n[1] else "").lower()
                tags = (n[3] if len(n) > 3 and n[3] else "").lower()
                if query in title or query in tags:
                    filtered.append(n)
            notes = filtered

        try:
            notes.sort(key=lambda x: x[self.col_index(self.sort_column)] or "", reverse=self.sort_reverse)
        except Exception:
            notes.sort(key=lambda x: x[0], reverse=self.sort_reverse)

        for note in notes:
            values = (
                note[0],
                note[1] if len(note) > 1 else "",
                note[2] if len(note) > 2 else "",
                note[3] if len(note) > 3 else "",
            )
            self.tree.insert("", "end", values=values)

    def sort_by(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False if column == "id" else True
        self.refresh_notes()

    def col_index(self, column):
        mapping = {"id": 0, "title": 1, "created": 2, "tags": 3}
        return mapping.get(column, 0)

    def show_context_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            try:
                self.menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu.grab_release()

    def open_selected_note(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        note_id = item["values"][0]
        note = self.service.get(note_id)
        if note:
            # передаём ссылку на settings, чтобы диалог мог обновлять общий флаг
            EditNoteDialog(self.frame, self.service, note, self.refresh_notes, settings=self.settings)

    def rename_note(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        note_id = item["values"][0]
        note = self.service.get(note_id)
        if not note:
            return

        win = tk.Toplevel(self.frame)
        win.title("Переименовать заметку")
        win.geometry("360x110")
        win.transient(self.frame)
        win.grab_set()

        ttk.Label(win, text="Новый заголовок:").pack(pady=(10, 5), padx=10, anchor="w")
        entry = ttk.Entry(win)
        entry.insert(0, note[1])
        entry.pack(fill="x", padx=10)

        def save_new_title():
            new_title = entry.get().strip()
            if not new_title:
                messagebox.showwarning("Ошибка", "Заголовок не может быть пустым")
                return
            content = note[2] if len(note) > 2 else ""
            tags = note[3] if len(note) > 3 else ""
            format_meta = note[4] if len(note) > 4 else "{}"
            try:
                self.service.update(note_id, new_title, content, tags, format_meta)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось переименовать: {e}")
                return
            self.refresh_notes()
            win.destroy()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Сохранить", command=save_new_title).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Отмена", command=win.destroy).pack(side="left", padx=6)

        self.frame.wait_window(win)

    def delete_note(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        note_id = item["values"][0]

        if self.ask_delete_confirm:
            confirmed, dont_ask = confirm_delete_dialog(
                self.frame,
                title="Подтверждение",
                message="Удалить заметку?",
                default_dont_ask=not self.ask_delete_confirm
            )
            if dont_ask:
                # обновляем общий settings и сохраняем
                self.ask_delete_confirm = False
                self.settings["ask_delete_confirm"] = False
                save_settings(self.settings)
            if not confirmed:
                return

        try:
            self.service.delete(note_id)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить заметку: {e}")
        finally:
            self.refresh_notes()

    def open_edit_window(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        note_id = item["values"][0]
        note = self.service.get(note_id)
        if note:
            EditNoteDialog(self.frame, self.service, note, self.refresh_notes, settings=self.settings)


class EditNoteDialog:
    def __init__(self, parent, service, note, refresh_callback, settings=None):
        self.service = service
        self.settings = settings if settings is not None else load_settings()
        self.refresh_callback = refresh_callback

        self.note_id = note[0]
        self.title = note[1] if len(note) > 1 else ""
        self.content = note[2] if len(note) > 2 else ""
        self.tags = note[3] if len(note) > 3 else ""
        self.format_meta = note[4] if len(note) > 4 else "{}"

        self.win = tk.Toplevel(parent)
        self.win.title("Редактирование заметки")
        # запрещаем горизонтальное изменение, разрешаем вертикальное
        self.win.resizable(False, True)
        self.win.geometry("520x380")
        self.win.transient(parent)
        self.win.grab_set()

        # корневой фрейм с padding
        root = ttk.Frame(self.win, padding=8)
        root.grid(row=0, column=0, sticky="nsew")
        self.win.columnconfigure(0, weight=1)
        self.win.rowconfigure(0, weight=1)

        # ряд 0: поля заголовка и тегов
        fields = ttk.Frame(root)
        fields.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        fields.columnconfigure(1, weight=1)

        ttk.Label(fields, text="Заголовок:").grid(row=0, column=0, sticky="w")
        self.title_entry = ttk.Entry(fields)
        self.title_entry.insert(0, self.title)
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ttk.Label(fields, text="Теги:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.tags_entry = ttk.Entry(fields)
        self.tags_entry.insert(0, self.tags)
        self.tags_entry.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=(6, 0))

        # ряд 1: содержимое (растягиваемый)
        content_frame = ttk.Frame(root)
        content_frame.grid(row=1, column=0, sticky="nsew")
        root.rowconfigure(1, weight=1)

        ttk.Label(content_frame, text="Содержимое:").pack(anchor="w", pady=(0, 4))
        self.content_text = tk.Text(content_frame, wrap="word")
        self.content_text.insert("1.0", self.content)
        self.content_text.pack(fill="both", expand=True)

        # ряд 2: панель кнопок (фиксированная высота)
        btn_frame = ttk.Frame(root)
        btn_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        btn_frame.columnconfigure(0, weight=1)  # позволяет прижимать кнопки вправо

        # кнопки — в колонках справа
        save_btn = ttk.Button(btn_frame, text="Сохранить", command=self.save_note)
        delete_btn = ttk.Button(btn_frame, text="Удалить", command=self.delete_note)
        cancel_btn = ttk.Button(btn_frame, text="Отмена", command=self.win.destroy)

        save_btn.grid(row=0, column=1, sticky="e", padx=4)
        delete_btn.grid(row=0, column=2, sticky="e", padx=4)
        cancel_btn.grid(row=0, column=3, sticky="e", padx=4)

        # бинды
        self.win.bind("<Control-s>", lambda e: self.save_note())
        self.win.bind("<Escape>", lambda e: self.win.destroy())

        # минимальные размеры: гарантируем место для заголовков, текста и кнопок
        self.win.update_idletasks()
        fields_h = fields.winfo_reqheight()
        buttons_h = btn_frame.winfo_reqheight()
        text_min = 120  # минимальная видимая высота текстовой области
        min_height = fields_h + buttons_h + text_min + 24  # запас на паддинги
        min_width = max(420, self.win.winfo_reqwidth())
        self.win.minsize(min_width, min_height)

        # фокус
        self.title_entry.focus_set()

    def save_note(self):
        title = self.title_entry.get().strip()
        tags = self.tags_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).rstrip("\n")
        if not title:
            messagebox.showwarning("Ошибка", "Заголовок не может быть пустым")
            return
        try:
            # поддерживаем интерфейс service.update(id, title, content, tags, format_meta)
            self.service.update(self.note_id, title, content, tags, self.format_meta)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить заметку: {e}")
            return
        # обновляем список в вызывающем UI и закрываем окно
        try:
            if callable(self.refresh_callback):
                self.refresh_callback()
        finally:
            self.win.destroy()

    def delete_note(self):
        current_flag = bool(self.settings.get("ask_delete_confirm", True))
        confirmed, dont_ask = confirm_delete_dialog(
            self.win,
            title="Подтверждение",
            message="Удалить заметку?",
            default_dont_ask=not current_flag
        )
        if dont_ask:
            # обновляем общий settings и сохраняем
            self.settings["ask_delete_confirm"] = False
            save_settings(self.settings)
        if not confirmed:
            return
        try:
            self.service.delete(self.note_id)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить заметку: {e}")
            return
        try:
            if callable(self.refresh_callback):
                self.refresh_callback()
        finally:
            self.win.destroy()
