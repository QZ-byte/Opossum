# ui/main_ui.py
import tkinter as tk
from tkinter import ttk

from services.db import Database
from services.notes_service import NotesService
from ui.notes_ui import NotesUI
from ui.passwords_ui import PasswordsUI


class RacconApp:
    def __init__(self, db_path: str = "raccon.db"):
        self.root = tk.Tk()
        self.root.title("Raccoon Pro")
        self.root.geometry("900x600")

        # --- сервисы ---
        self.db = Database(db_path)
        self.notes_service = NotesService(self.db)

        # --- Notebook (вкладки) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # --- Заметки ---
        self.notes_tab = NotesUI(self.notebook, self.notes_service)
        self.notebook.add(self.notes_tab.frame, text="Заметки")

        # --- Задачи (пока пустая) ---
        self.tasks_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tasks_tab, text="Задачи")

        # --- Пароли ---
        # Подключаем PasswordsUI вместо пустого Frame
        # master_password можно будет вынести в отдельный ввод/настройки
        self.passwords_tab = PasswordsUI(self.notebook, master_password="secret123")
        self.notebook.add(self.passwords_tab.get_frame(), text="Пароли")

        # --- DCLI кнопка ---
        dcli_btn = ttk.Button(self.root, text="DCLI", command=self.open_dcli)
        dcli_btn.pack(side="bottom", pady=4)

    def open_dcli(self):
        from ui.dev_cli import DevCLI
        DevCLI(self.root, db=self.db, notes_service=self.notes_service)

    def run(self):
        self.root.mainloop()
