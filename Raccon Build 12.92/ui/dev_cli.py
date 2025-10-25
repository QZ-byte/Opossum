# ui/dev_cli.py
"""
DevCLI - небольшая встроенная консоль для разработчика.

Команды:
  help                       - показать список команд
  tables                     - показать таблицы в sqlite
  notes                      - вывести все заметки
  sql <запрос>               - выполнить SQL запрос и показать результаты
  dump                       - вывести содержимое .py файлов в окно
  dump save                  - сохранить каждый .py в dcli_dumps/<name>.txt
  dump all [имя_файла]       - собрать все .py в один файл dcli_dumps/all_code_<ts>.txt
  debug                      - открыть окно Debugger (графический)
  clear                      - очистить окно вывода
"""
import os
import sys
import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk

# Внутренний helper для работы с БД (ожидается, что передаётся объект с методом fetchall)
class _SafeDB:
    def __init__(self, db_obj):
        self._db = db_obj

    def fetchall(self, query: str):
        # Поддерживаем два варианта: объект Database с методом fetchall или sqlite3.Connection
        if self._db is None:
            raise RuntimeError("DB not provided")
        if hasattr(self._db, "fetchall"):
            return self._db.fetchall(query)
        # Если передан sqlite3.Connection
        cur = self._db.cursor()
        cur.execute(query)
        return cur.fetchall()


class DevCLI:
    def __init__(self, master, db=None, notes_service=None):
        """
        master      - parent TK widget (обычно root или frame)
        db          - объект базы данных либо sqlite3.Connection; должен поддерживать fetchall(query)
        notes_service - сервис заметок с методом get_all_notes()
        """
        self.master = master
        self.db = _SafeDB(db) if db is not None else None
        self.notes_service = notes_service

        self.win = tk.Toplevel(master)
        self.win.title("DCLI")
        self.win.geometry("900x520")

        # Текстовый вывод (консоль)
        self.output = tk.Text(self.win, wrap="word", state="disabled",
                              bg="black", fg="lime", insertbackground="lime", padx=6, pady=6)
        self.output.pack(fill="both", expand=True, padx=6, pady=(6, 0))

        # Панель ввода
        entry_frame = ttk.Frame(self.win)
        entry_frame.pack(fill="x", padx=6, pady=6)

        self.cmd_entry = ttk.Entry(entry_frame)
        self.cmd_entry.pack(side="left", fill="x", expand=True)
        self.cmd_entry.bind("<Return>", self._on_enter)

        ttk.Button(entry_frame, text="Выполнить", command=self._run_cmd).pack(side="left", padx=6)
        ttk.Button(entry_frame, text="Очистить", command=self._clear).pack(side="left")

        # Начальное сообщение
        self._print("ГОТОВ. Введите 'help' для списка команд.")

    # ----------------- базовые утилиты -----------------
    def _print(self, text: str):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _clear(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _on_enter(self, _event=None):
        self._run_cmd()

    def _run_cmd(self):
        cmd = self.cmd_entry.get().strip()
        self.cmd_entry.delete(0, "end")
        self.execute(cmd)

    # ----------------- основной парсер команд -----------------
    def execute(self, cmd: str):
        if not cmd:
            return
        self._print(f"> {cmd}")

        parts = cmd.split()
        head = parts[0].lower()

        try:
            if head == "help":
                self._cmd_help()
            elif head == "tables":
                self._cmd_tables()
            elif head == "notes":
                self._cmd_notes()
            elif head == "sql":
                self._cmd_sql(" ".join(parts[1:]))
            elif head == "dump":
                # Подкоманды: dump, dump save, dump all
                if len(parts) == 1:
                    self._dump_code(print_only=True)
                elif parts[1] == "save":
                    self._dump_code(print_only=False)
                elif parts[1] == "all":
                    name = parts[2] if len(parts) > 2 else None
                    path = self._dump_code_all(out_filename=name)
                    self._print(f"[dump all] Сохранено в: {path}")
                else:
                    self._print("Использование: dump | dump save | dump all [имя_файла]")
            elif head == "debug":
                self._cmd_debug()
            elif head == "clear":
                self._clear()
            else:
                self._print("Неизвестная команда. help — список команд.")
        except Exception as e:
            self._print(f"[ERROR] {e}")

    # ----------------- реализации команд -----------------
    def _cmd_help(self):
        lines = [
            "Команды:",
            "  help                       - показать этот список",
            "  tables                     - показать таблицы sqlite",
            "  notes                      - вывести все заметки",
            "  sql <запрос>               - выполнить SQL запрос",
            "  dump                       - вывести .py в окно",
            "  dump save                  - сохранить каждый .py в dcli_dumps/",
            "  dump all [имя_файла]       - собрать все .py в один файл",
            "  debug                      - открыть Debugger окно",
            "  clear                      - очистить окно вывода"
        ]
        for l in lines:
            self._print(l)

    def _cmd_tables(self):
        if self.db is None:
            self._print("[tables] DB не предоставлена")
            return
        try:
            rows = self.db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
            names = ", ".join(r[0] for r in rows) if rows else "(нет таблиц)"
            self._print("Таблицы: " + names)
        except Exception as e:
            self._print(f"[tables] Ошибка: {e}")

    def _cmd_notes(self):
        if self.notes_service is None:
            self._print("[notes] notes_service не предоставлен")
            return
        try:
            notes = self.notes_service.get_all_notes()
            if not notes:
                self._print("(нет заметок)")
                return
            for n in notes:
                self._print(str(n))
        except Exception as e:
            self._print(f"[notes] Ошибка: {e}")

    def _cmd_sql(self, query: str):
        if not query:
            self._print("Использование: sql <запрос>")
            return
        if self.db is None:
            self._print("[sql] DB не предоставлена")
            return
        try:
            rows = self.db.fetchall(query)
            if not rows:
                self._print("(пусто)")
                return
            for r in rows:
                self._print(str(tuple(r)))
        except sqlite3.Error as e:
            self._print(f"[SQL Error] {e}")
        except Exception as e:
            self._print(f"[sql] Ошибка: {e}")

    def _cmd_debug(self):
        # Открываем отдельное окно DebugUI; используем относительный импорт внутри пакета ui
        try:
            from .debug_ui import DebugUI
        except Exception:
            # fallback: попробуем импорт как корневой модуль (если dev_cli.py не в ui/)
            try:
                import importlib, os
                sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                DebugUI = importlib.import_module("ui.debug_ui").DebugUI
            except Exception as e:
                self._print(f"[debug] Не удалось импортировать DebugUI: {e}")
                return

        # Удерживаем ссылку на окно, чтобы оно не было собранным GC
        if not hasattr(self, "_debug_window") or self._debug_window is None or not self._debug_window.win.winfo_exists():
            try:
                self._debug_window = DebugUI(self.win if hasattr(self, "win") else self.master)
                self._print("[debug] Окно Debugger открыто")
            except Exception as e:
                self._print(f"[debug] Ошибка при создании окна: {e}")
        else:
            try:
                self._debug_window.win.lift()
                self._print("[debug] Окно Debugger поднято на передний план")
            except Exception:
                pass

    # ----------------- дамп кода по файлам -----------------
    def _dump_code(self, print_only: bool = True):
        """
        Обходит проект от корня (родитель папки ui/) и:
          - print_only=True: печатает содержимое .py файлов в окно.
          - print_only=False: сохраняет каждый .py в dcli_dumps/<имя>.txt
        """
        try:
            root_dir = os.path.dirname(os.path.dirname(__file__))
            dump_dir = os.path.join(root_dir, "dcli_dumps")
            if not print_only:
                os.makedirs(dump_dir, exist_ok=True)

            for dirpath, _, files in os.walk(root_dir):
                # пропускаем __pycache__ и скрытые каталоги
                if os.path.basename(dirpath).startswith("__pycache__"):
                    continue
                for fname in sorted(files):
                    if not fname.endswith(".py"):
                        continue
                    path = os.path.join(dirpath, fname)
                    rel = os.path.relpath(path, root_dir)
                    try:
                        with open(path, "r", encoding="utf-8") as fh:
                            content = fh.read()
                    except Exception as e:
                        self._print(f"[dump] Ошибка чтения {rel}: {e}")
                        continue

                    if print_only:
                        self._print(f"\n--- {rel} ---")
                        # печатаем содержимое построчно, чтобы не раздувать память
                        for line in content.splitlines():
                            self._print(line)
                    else:
                        out_path = os.path.join(dump_dir, fname.replace(".py", ".txt"))
                        try:
                            with open(out_path, "w", encoding="utf-8") as out:
                                out.write(content)
                            self._print(f"Сохранено: {out_path}")
                        except Exception as e:
                            self._print(f"[dump save] Ошибка записи {out_path}: {e}")

            self._print("[dump] Готово.")
        except Exception as e:
            self._print(f"[dump] Ошибка: {e}")

    # ----------------- объединённый дамп всех файлов в один -----------------
    def _dump_code_all(self, out_filename: str = None) -> str:
        """
        Собирает все .py файлы проекта в один файл.
        Возвращает путь к сохранённому файлу.
        """
        root_dir = os.path.dirname(os.path.dirname(__file__))
        dumps_dir = os.path.join(root_dir, "dcli_dumps")
        os.makedirs(dumps_dir, exist_ok=True)

        if out_filename:
            safe_name = out_filename
        else:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = f"all_code_{ts}.txt"

        out_path = os.path.join(dumps_dir, safe_name)

        with open(out_path, "w", encoding="utf-8") as out_f:
            header = (
                f"All project .py files dump\nGenerated: {datetime.datetime.now().isoformat()}\n"
                f"Project root: {root_dir}\n\n"
            )
            out_f.write(header)
            for dirpath, _, files in os.walk(root_dir):
                # пропускаем виртуальные и системные каталоги
                base = os.path.basename(dirpath)
                if base.startswith("__pycache__") or base.startswith("."):
                    continue
                rel_dir = os.path.relpath(dirpath, root_dir)
                for fname in sorted(files):
                    if not fname.endswith(".py"):
                        continue
                    file_path = os.path.join(dirpath, fname)
                    rel_path = os.path.join(rel_dir, fname) if rel_dir != "." else fname
                    out_f.write(f"\n--- FILE: {rel_path} ---\n")
                    try:
                        with open(file_path, "r", encoding="utf-8") as fh:
                            out_f.write(fh.read() + "\n")
                    except Exception as e:
                        out_f.write(f"[ERROR reading file: {e}]\n")

        return out_path
