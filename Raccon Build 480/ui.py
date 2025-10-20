# ui.py
import tkinter as tk
from tkinter import ttk

from services.db import Database
from services.notes_service import NotesService
from notes_ui import NotesUI
from dev_cli import DevCLI

class RacconApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Raccon Pre α")
        self.root.geometry("900x600")

        # --- сервисы ---
        self.db = Database("raccon.db")
        self.notes_service = NotesService(self.db)

        # --- вкладки ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Заметки
        self.notes_tab = NotesUI(self.notebook, self.notes_service)
        self.notebook.add(self.notes_tab.frame, text="Заметки")

        # Заглушки для будущих модулей
        self.tasks_tab = ttk.Frame(self.notebook)
        self.passwords_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tasks_tab, text="Задачи")
        self.notebook.add(self.passwords_tab, text="Пароли")

        # --- нижняя панель с кнопками ---
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", side="bottom", pady=6, padx=6)

        dev_btn = ttk.Button(bottom_frame, text="Dev CLI", command=self.open_cli)
        dev_btn.pack(side="right")

    def open_cli(self):
        DevCLI(self.root, db=self.db, notes_service=self.notes_service)

    def run(self):
        self.root.mainloop()
