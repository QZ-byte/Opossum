# dev_cli.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
from code_tools import save_code_snapshot

class DevCLI(tk.Toplevel):
    def __init__(self, master=None, db=None, notes_service=None):
        super().__init__(master)
        self.title("Developer CLI")
        self.geometry("420x320")
        self.resizable(False, False)
        self.db = db
        self.notes_service = notes_service

        ttk.Label(self, text="Выберите опцию:", font=("Arial", 12, "bold")).pack(pady=10)

        options = [
            ("Dump Code Snapshot", self.run_dump),
            ("Показать информацию о проекте", self.show_info),
            ("Очистить базу данных", self.clear_db),
            ("Экспорт заметок в Markdown", self.export_notes_md),
            ("Закрыть CLI", self.close_cli),
        ]

        for text, cmd in options:
            ttk.Button(self, text=text, command=cmd).pack(fill="x", padx=20, pady=6)

    def run_dump(self):
        try:
            save_code_snapshot()
            messagebox.showinfo("Готово", "Снимок кода сохранён в code_snapshot.txt")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.destroy()

    def show_info(self):
        try:
            cwd = os.getcwd()
            db_path = getattr(self.db, "path", "—")
            note_count = 0
            if self.notes_service:
                rows = self.notes_service.get_all_notes()
                note_count = len(rows) if rows else 0
            info = f"Текущая папка: {cwd}\nDB: {db_path}\nЗаметок: {note_count}"
            messagebox.showinfo("Инфо", info)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.destroy()

    def clear_db(self):
        try:
            path = getattr(self.db, "path", None)
            if path and os.path.exists(path):
                self.db.close()
                os.remove(path)
                messagebox.showinfo("OK", "Файл БД удалён")
            else:
                messagebox.showwarning("Нет файла", "Файл базы данных не найден")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.destroy()

    def export_notes_md(self):
        try:
            if not self.notes_service:
                raise RuntimeError("NotesService не передан")
            notes = self.notes_service.get_all_notes_full()
            out_lines = []
            for n in notes:
                nid, title, content, tags, created_at = n
                out_lines.append(f"# {title}\n\n_Теги: {tags} | Создано: {created_at}_\n\n{content}\n\n---\n")
            out_path = os.path.join(os.getcwd(), "notes_export.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(out_lines))
            messagebox.showinfo("Экспорт", f"Заметки экспортированы в {out_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            self.destroy()

    def close_cli(self):
        self.destroy()
