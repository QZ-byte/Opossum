# ui.py
import tkinter as tk
from tkinter import ttk
from services.db import Database
from services.notes_service import NotesService
from notes_ui import NotesUI

class RacconApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Raccon Pre a")
        self.root.geometry("800x600")

        # сервисы
        self.db = Database()
        self.notes_service = NotesService(self.db)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # вкладки
        self.notes_tab = NotesUI(self.notebook, self.notes_service)
        self.notebook.add(self.notes_tab.frame, text="Заметки")

        # заглушки
        self.tasks_tab = ttk.Frame(self.notebook)
        self.passwords_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tasks_tab, text="Задачи")
        self.notebook.add(self.passwords_tab, text="Пароли")

    def run(self):
        self.root.mainloop()
