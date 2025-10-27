# ui/passwords_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from services.paws.passwords_service import PasswordsService
from services.paws.generator import generate_password


class PasswordsUI:
    def __init__(self, master, master_password: str, db_path: str, default_gen_len: int = 16):
        self.master = master
        self.master_password = master_password
        self.db_path = db_path
        self.service = PasswordsService(master_password, db_path=db_path)
        self.default_gen_len = default_gen_len

        self.frame = ttk.Frame(master)
        self.sort_col = "id"
        self.sort_asc = True
        self._current_query: Optional[str] = None

        self._build_ui()
        self.load_entries()

    def get_frame(self):
        return self.frame

    # UI construction
    def _build_ui(self):
        top = ttk.Frame(self.frame)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Сервис:").pack(side="left")
        self.service_entry = ttk.Entry(top, width=22)
        self.service_entry.pack(side="left", padx=6)

        ttk.Label(top, text="Логин:").pack(side="left")
        self.username_entry = ttk.Entry(top, width=22)
        self.username_entry.pack(side="left", padx=6)

        ttk.Button(top, text="Добавить", command=self.add_entry).pack(side="left", padx=6)
        ttk.Button(top, text="Сгенерировать", command=self._generate_into_clipboard).pack(side="left")

        # Search
        ttk.Label(top, text="Поиск:").pack(side="left", padx=(20, 0))
        self.search_entry = ttk.Entry(top, width=24)
        self.search_entry.pack(side="left", padx=6)
        ttk.Button(top, text="Искать", command=self.search_entries).pack(side="left", padx=4)
        ttk.Button(top, text="Сброс", command=self.reset_search).pack(side="left")

        # Table
        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill="both", expand=True, padx=8, pady=6)

        cols = ("id", "service", "username", "notes", "updated_at")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=16)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Headings with sort callbacks
        self.tree.heading("id", text="ID", command=lambda: self.sort_by("id"))
        self.tree.heading("service", text="Сервис", command=lambda: self.sort_by("service"))
        self.tree.heading("username", text="Логин", command=lambda: self.sort_by("username"))
        self.tree.heading("notes", text="Заметки", command=lambda: self.sort_by("notes"))
        self.tree.heading("updated_at", text="Обновлено", command=lambda: self.sort_by("updated_at"))

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("service", width=200, anchor="w")
        self.tree.column("username", width=180, anchor="w")
        self.tree.column("notes", width=260, anchor="w")
        self.tree.column("updated_at", width=140, anchor="center")

        self.tree.bind("<Double-1>", self.open_entry_card)

        # Bottom actions
        bottom = ttk.Frame(self.frame)
        bottom.pack(fill="x", padx=8, pady=8)
        ttk.Button(bottom, text="Показать пароль", command=self.show_password).pack(side="left")
        ttk.Button(bottom, text="Копировать пароль", command=self.copy_password).pack(side="left", padx=6)
        ttk.Button(bottom, text="Удалить", command=self.delete_entry).pack(side="left", padx=6)

    # Helpers
    def _top_level(self):
        return self.frame.winfo_toplevel()

    def _get_selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(self.tree.item(sel[0])["values"][0])
        except Exception:
            return None

    # Load / refresh
    def load_entries(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            rows = self.service.list_entries(query=self._current_query, sort_by=self.sort_col, ascending=self.sort_asc)
            for row in rows:
                # rows may or may not include updated_at depending on DB; normalize to 5 values
                vals = list(row)
                if len(vals) == 4:
                    vals.append("")  # ensure updated_at column exists for Treeview
                self.tree.insert("", "end", values=vals)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить пароли: {e}")

    def sort_by(self, col: str):
        if self.sort_col == col:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_col = col
            self.sort_asc = True
        self.load_entries()

    def search_entries(self):
        q = self.search_entry.get().strip()
        self._current_query = q if q else None
        self.load_entries()

    def reset_search(self):
        self.search_entry.delete(0, "end")
        self._current_query = None
        self.load_entries()

    # CRUD
    def add_entry(self):
        service_name = self.service_entry.get().strip()
        username = self.username_entry.get().strip()
        if not service_name:
            messagebox.showwarning("Ошибка", "Сервис не может быть пустым")
            return

        # если пароль не введён — генерируем автоматически
        pwd = generate_password(length=self.default_gen_len, digits=True, upper=True, symbols=True)

        try:
            new_id = self.service.add_entry(service_name, username, pwd)
            self.service_entry.delete(0, "end")
            self.username_entry.delete(0, "end")
            self.load_entries()
            messagebox.showinfo("Добавлено", f"Запись #{new_id} создана. Пароль сгенерирован автоматически.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить запись: {e}")

    def delete_entry(self):
        entry_id = self._get_selected_id()
        if not entry_id:
            messagebox.showwarning("Ошибка", "Выберите запись для удаления")
            return
        if not messagebox.askyesno("Подтвердите", f"Удалить запись #{entry_id}?"):
            return
        try:
            self.service.delete_entry(entry_id)
            self.load_entries()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить запись: {e}")

    # Password ops
    def show_password(self):
        entry_id = self._get_selected_id()
        if not entry_id:
            messagebox.showwarning("Ошибка", "Выберите запись")
            return
        entry = self.service.get_entry_by_id(entry_id)
        if not entry:
            messagebox.showerror("Ошибка", "Запись не найдена")
            return
        messagebox.showinfo("Пароль", f"Сервис: {entry['service']}\nЛогин: {entry['username']}\nПароль: {entry['password']}")

    def copy_password(self):
        entry_id = self._get_selected_id()
        if not entry_id:
            messagebox.showwarning("Ошибка", "Выберите запись")
            return
        entry = self.service.get_entry_by_id(entry_id)
        if not entry:
            messagebox.showerror("Ошибка", "Запись не найдена")
            return

        pwd = entry["password"]
        root = self._top_level()
        try:
            root.clipboard_clear()
            root.clipboard_append(pwd)
            messagebox.showinfo("Копирование", "Пароль скопирован в буфер обмена (очистится через 3 минуты)")
            root.after(180_000, lambda: self._safe_clipboard_clear(root))
        except Exception as e:
            messagebox.showerror("Копирование", f"Не удалось скопировать пароль: {e}")

    def _safe_clipboard_clear(self, root):
        try:
            if root.winfo_exists():
                root.clipboard_clear()
        except Exception:
            pass

    # Generate helper (places generated password into clipboard for quick paste)
    def _generate_into_clipboard(self):
        pwd = generate_password(length=self.default_gen_len, digits=True, upper=True, symbols=True)
        root = self._top_level()
        try:
            root.clipboard_clear()
            root.clipboard_append(pwd)
            messagebox.showinfo("Генерация", "Пароль сгенерирован и скопирован в буфер обмена (очистится через 3 минуты)")
            root.after(180_000, lambda: self._safe_clipboard_clear(root))
        except Exception as e:
            messagebox.showerror("Генерация", f"Не удалось скопировать сгенерированный пароль: {e}")

    # Double-click card
    def open_entry_card(self, event=None):
        sel_id = self._get_selected_id()
        if not sel_id:
            return
        entry = self.service.get_entry_by_id(sel_id)
        if not entry:
            messagebox.showerror("Ошибка", "Запись не найдена")
            return

        win = tk.Toplevel(self.frame)
        win.title(f"Запись #{entry['id']}")
        win.geometry("520x380")
        win.transient(self.frame)

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        def ro_field(parent, label_text, value):
            box = ttk.Frame(parent)
            box.pack(fill="x", pady=4)
            ttk.Label(box, text=label_text, width=12).pack(side="left")
            e = ttk.Entry(box)
            e.pack(side="left", fill="x", expand=True)
            e.insert(0, value or "")
            e.configure(state="readonly")
            return e

        ro_field(frm, "Сервис:", entry["service"])
        ro_field(frm, "Логин:", entry["username"])
        ro_field(frm, "Создано:", entry.get("created_at", ""))
        ro_field(frm, "Обновлено:", entry.get("updated_at", ""))

        pbox = ttk.LabelFrame(frm, text="Пароль")
        pbox.pack(fill="x", pady=8)
        pwd_entry = ttk.Entry(pbox, show="*")
        pwd_entry.pack(side="left", fill="x", expand=True, padx=6, pady=6)
        pwd_entry.insert(0, entry["password"])

        def toggle():
            pwd_entry.configure(show="" if pwd_entry.cget("show") == "*" else "*")

        ttk.Button(pbox, text="Показать", command=toggle).pack(side="left", padx=6)
        ttk.Button(pbox, text="Копировать", command=lambda: self._copy_from_card(win, entry["password"])).pack(side="left")

        nbox = ttk.LabelFrame(frm, text="Заметки")
        nbox.pack(fill="both", expand=True, pady=8)
        notes_text = tk.Text(nbox, height=6, wrap="word")
        notes_text.pack(fill="both", expand=True, padx=6, pady=6)
        notes_text.insert("1.0", entry.get("notes", "") or "")
        notes_text.configure(state="disabled")

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Закрыть", command=win.destroy).pack(side="right")

    def _copy_from_card(self, win, pwd: str):
        root = self._top_level()
        try:
            root.clipboard_clear()
            root.clipboard_append(pwd)
            messagebox.showinfo("Копирование", "Пароль скопирован (очистится через 3 минуты)")
            root.after(180_000, lambda: self._safe_clipboard_clear(root))
        except Exception as e:
            messagebox.showerror("Копирование", f"Не удалось скопировать пароль: {e}")
