# ui/main_ui.py
import tkinter as tk
from tkinter import ttk

from services.db import Database
from services.notes_service import NotesService
from .notes_ui import NotesUI
from .dev_cli import DevCLI


class RacconApp:
    """
    Главное окно приложения.
    Базовый минимум: вкладка 'Заметки' + кнопка DCLI для отладки.
    """

    def __init__(self, db_path: str = "raccon.db"):
        # Корневое окно
        self.root = tk.Tk()
        self.root.title("Raccon Pro")
        self.root.geometry("900x600")

        # Инициализация сервисов
        self.db = Database(db_path)
        self.notes_service = NotesService(self.db)

        # Основной Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Вкладка: Заметки
        self.notes_tab = NotesUI(self.notebook, self.notes_service)
        self.notebook.add(self.notes_tab.frame, text="Заметки")

        # Заглушки под будущие модули
        self.tasks_tab = ttk.Frame(self.notebook)
        self.passwords_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tasks_tab, text="Задачи")
        self.notebook.add(self.passwords_tab, text="Пароли")

        # Нижняя панель с кнопкой DCLI
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", side="bottom", pady=4)

        dcli_btn = ttk.Button(bottom_frame, text="DCLI", command=self.open_cli)
        dcli_btn.pack(side="left", padx=6)

    def open_cli(self):
        # Открываем DevCLI в отдельном окне
        DevCLI(self.root, db=self.db, notes_service=self.notes_service)

    def run(self):
        self.root.mainloop()
