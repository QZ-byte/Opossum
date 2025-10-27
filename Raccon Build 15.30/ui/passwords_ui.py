import tkinter as tk
from tkinter import ttk, messagebox
from services.paws.passwords_service import PasswordsService
from services.paws.generator import generate_password


class PasswordsUI:
    def __init__(self, master, master_password: str):
        self.master = master
        self.service = PasswordsService(master_password)

        self.frame = ttk.Frame(master)

        # Верхняя панель управления
        control = ttk.Frame(self.frame)
        control.pack(fill="x", padx=8, pady=8)

        ttk.Label(control, text="Сервис:").pack(side="left")
        self.service_entry = ttk.Entry(control, width=20)
        self.service_entry.pack(side="left", padx=6)

        ttk.Label(control, text="Логин:").pack(side="left")
        self.username_entry = ttk.Entry(control, width=20)
        self.username_entry.pack(side="left", padx=6)

        ttk.Button(control, text="Добавить", command=self.add_entry).pack(side="left", padx=6)
        ttk.Button(control, text="Сгенерировать", command=self.generate_and_insert).pack(side="left", padx=6)

        # Таблица
        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill="both", expand=True, padx=8, pady=6)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "service", "username", "notes"),
            show="headings",
            height=16
        )
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.heading("id", text="ID")
        self.tree.heading("service", text="Сервис")
        self.tree.heading("username", text="Логин")
        self.tree.heading("notes", text="Заметки")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("service", width=160, anchor="w")
        self.tree.column("username", width=160, anchor="w")
        self.tree.column("notes", width=200, anchor="w")

        # Нижняя панель
        bottom = ttk.Frame(self.frame)
        bottom.pack(fill="x", padx=8, pady=8)

        ttk.Button(bottom, text="Показать пароль", command=self.show_password).pack(side="left")
        ttk.Button(bottom, text="Удалить", command=self.delete_entry).pack(side="left", padx=6)

        self.load_entries()

    def get_frame(self):
        return self.frame

    # ---------------- CRUD ----------------
    def load_entries(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            rows = self.service.list_entries()
            for note in rows:
                self.tree.insert("", "end", values=note)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить пароли: {e}")

    def add_entry(self):
        service = self.service_entry.get().strip()
        username = self.username_entry.get().strip()
        if not service:
            messagebox.showwarning("Ошибка", "Сервис не может быть пустым")
            return
        # генерируем пароль сразу
        password = generate_password()
        self.service.add_entry(service, username, password)
        self.service_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.load_entries()
        messagebox.showinfo("Добавлено", f"Пароль для {service} создан и сохранён")

    def generate_and_insert(self):
        pwd = generate_password()
        self.username_entry.insert(0, f"gen:{pwd}")

    def show_password(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите запись")
            return
        entry_id = self.tree.item(sel[0])["values"][0]
        entry = self.service.get_entry_by_id(entry_id)
        if not entry:
            messagebox.showerror("Ошибка", "Запись не найдена")
            return
        messagebox.showinfo("Пароль", f"Сервис: {entry['service']}\nЛогин: {entry['username']}\nПароль: {entry['password']}")

    def delete_entry(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите запись для удаления")
            return
        entry_id = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Подтвердите", "Удалить выбранную запись?"):
            self.service.delete_entry(entry_id)
            self.load_entries()
