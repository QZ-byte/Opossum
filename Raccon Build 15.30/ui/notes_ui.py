# ui/notes_ui.py
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class FormattingPanel(tk.Toplevel):
    """Полноценное окно форматирования с Pin/Unpin.
    При Pin панель следует за окном редактора, при этом сохраняет свой текущий размер.
    """
    WIDTH = 300
    DEFAULT_HEIGHT = 420

    def __init__(self, editor_win: tk.Toplevel, text_widget: tk.Text, format_meta: dict | None):
        super().__init__(editor_win)
        self.editor_win = editor_win
        self.text = text_widget
        self.format_meta = format_meta or {}
        self.pinned = False
        self._following = False
        self._editor_configure_handler = None

        self.title("Панель форматирования")
        self.geometry(f"{self.WIDTH}x{self.DEFAULT_HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self.withdraw()  # скрыта по умолчанию

        # Если редактор уничтожается — закрыть панель
        try:
            self.editor_win.bind("<Destroy>", lambda e: self.destroy(), add="+")
        except Exception:
            pass

        self._build_ui()
        self._ensure_tags()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill="both", expand=True)

        header = ttk.Frame(frm)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="Панель форматирования", font=("", 10, "bold")).pack(side="left")
        self.pin_btn = ttk.Button(header, text="Pin", width=8, command=self._toggle_pin)
        self.pin_btn.pack(side="right")

        ttk.Separator(frm, orient="horizontal").pack(fill="x", pady=(6, 8))

        ttk.Button(frm, text="Жирный", command=lambda: self.apply_style("bold")).pack(fill="x", pady=4)
        ttk.Button(frm, text="Курсив", command=lambda: self.apply_style("italic")).pack(fill="x", pady=4)
        ttk.Button(frm, text="Подчёркнутый", command=lambda: self.apply_style("underline")).pack(fill="x", pady=4)
        ttk.Button(frm, text="Зачёркнутый", command=lambda: self.apply_style("strike")).pack(fill="x", pady=4)

        ttk.Separator(frm, orient="horizontal").pack(fill="x", pady=(8, 8))
        ttk.Button(frm, text="Очистить формат", command=self.clear_meta).pack(fill="x", pady=4)
        ttk.Button(frm, text="Закрыть панель", command=self.hide).pack(fill="x", pady=(8, 0))

    def _ensure_tags(self):
        try:
            self.text.tag_configure("fmt_bold", font=("Segoe UI", 10, "bold"))
            self.text.tag_configure("fmt_italic", font=("Segoe UI", 10, "italic"))
            self.text.tag_configure("fmt_underline", underline=1)
            self.text.tag_configure("fmt_strike", overstrike=1)
        except Exception:
            pass

    # ---------------- Pin / follow logic ----------------
    def _toggle_pin(self):
        self.pinned = not self.pinned
        self.pin_btn.config(text="Unpin" if self.pinned else "Pin")
        if self.pinned:
            try:
                self.transient(self.editor_win)
            except Exception:
                pass
            self._start_following_editor()
        else:
            try:
                self.transient(None)
            except Exception:
                pass
            self._stop_following_editor()

    def _start_following_editor(self):
        if self._following:
            return
        self._following = True

        def _on_editor_configure(event=None):
            try:
                self.editor_win.update_idletasks()
                ex = self.editor_win.winfo_rootx()
                ey = self.editor_win.winfo_rooty()
                ew = self.editor_win.winfo_width()
                eh = self.editor_win.winfo_height()
                if ew <= 1 or eh <= 1:
                    return
                # сохраняем текущие размеры панели, чтобы не перезаписывать пользовательские настройки
                try:
                    cur_w = max(self.winfo_width(), 1)
                    cur_h = max(self.winfo_height(), 1)
                    if cur_w <= 1:
                        cur_w = self.WIDTH
                    if cur_h <= 1:
                        cur_h = eh
                except Exception:
                    cur_w = self.WIDTH
                    cur_h = eh
                px = ex + ew + 10
                py = ey
                # Меняем только позицию, сохраняя размеры
                self.geometry(f"{cur_w}x{cur_h}+{px}+{py}")
            except Exception:
                pass

        # Сохраняем обработчик для возможности отписки
        self._editor_configure_handler = _on_editor_configure
        try:
            self.editor_win.bind("<Configure>", self._editor_configure_handler, add="+")
            self._editor_configure_handler()
        except Exception:
            # fallback: попытка позиционировать один раз
            try:
                self._position_right_of_editor()
            except Exception:
                pass

    def _stop_following_editor(self):
        if not self._following:
            return
        self._following = False
        try:
            if self._editor_configure_handler:
                # Попытка удалить конкретный обработчик; tkinter не всегда гарантирует удаление по ссылке
                self.editor_win.unbind("<Configure>", self._editor_configure_handler)
        except Exception:
            try:
                # Грубый fallback: удалить все Configure-обработчики
                self.editor_win.unbind("<Configure>")
            except Exception:
                pass
        finally:
            self._editor_configure_handler = None

    def _position_right_of_editor(self):
        try:
            ex = self.editor_win.winfo_rootx()
            ey = self.editor_win.winfo_rooty()
            ew = self.editor_win.winfo_width()
            eh = self.editor_win.winfo_height()
            if ew <= 1 or eh <= 1:
                self.after(30, self._position_right_of_editor)
                return
            px = ex + ew + 10
            py = ey
            # при первоначальном позиционировании используем текущие размеры панели
            try:
                cur_w = max(self.winfo_width(), 1)
                cur_h = max(self.winfo_height(), 1)
                if cur_w <= 1:
                    cur_w = self.WIDTH
                if cur_h <= 1:
                    cur_h = eh
            except Exception:
                cur_w = self.WIDTH
                cur_h = eh
            self.geometry(f"{cur_w}x{cur_h}+{px}+{py}")
        except Exception:
            pass

    def show(self):
        if self.pinned:
            self._position_right_of_editor()
        self.deiconify()
        self.lift()
        self._apply_all_meta_tags()

    def hide(self):
        self.withdraw()

    # ---------------- форматирование метаданных ----------------
    def _index_to_offset(self, idx: str) -> int:
        line, col = map(int, str(idx).split("."))
        offset = 0
        for l in range(1, line):
            line_text = self.text.get(f"{l}.0", f"{l}.end")
            offset += len(line_text) + 1
        offset += col
        return offset

    def _offset_to_index(self, offset: int) -> str:
        line = 1
        while True:
            line_text = self.text.get(f"{line}.0", f"{line}.end")
            line_len = len(line_text) + 1
            if offset < line_len:
                col = offset
                return f"{line}.{col}"
            offset -= line_len
            line += 1

    def _get_selection_bounds_offsets(self):
        try:
            s = self.text.index("sel.first")
            e = self.text.index("sel.last")
        except tk.TclError:
            return None
        return self._index_to_offset(s), self._index_to_offset(e)

    def _record_range(self, style: str, start_off: int, end_off: int):
        if start_off >= end_off:
            return
        lst = self.format_meta.get(style, [])
        lst.append([start_off, end_off])
        self.format_meta[style] = lst
        self._apply_meta_tag(style, start_off, end_off)

    def apply_style(self, style_key: str):
        bounds = self._get_selection_bounds_offsets()
        if not bounds:
            messagebox.showinfo("Форматирование", "Выделите текст, который нужно отформатировать")
            return
        start_off, end_off = bounds
        self._record_range(style_key, start_off, end_off)

    def clear_meta(self):
        if not messagebox.askyesno("Очистка", "Удалить все метаданные форматирования?"):
            return
        self.format_meta.clear()
        self._remove_all_meta_tags()
        messagebox.showinfo("Очистка", "Метаданные удалены")

    def _apply_meta_tag(self, style: str, start_off: int, end_off: int):
        tag = self._style_to_tag(style)
        try:
            start_idx = self._offset_to_index(start_off)
            end_idx = self._offset_to_index(end_off)
            self.text.tag_add(tag, start_idx, end_idx)
        except Exception:
            pass

    def _apply_all_meta_tags(self):
        self._remove_all_meta_tags()
        for style, ranges in self.format_meta.items():
            for r in ranges:
                try:
                    self._apply_meta_tag(style, int(r[0]), int(r[1]))
                except Exception:
                    pass

    def _remove_all_meta_tags(self):
        for tag in ("fmt_bold", "fmt_italic", "fmt_underline", "fmt_strike"):
            try:
                self.text.tag_remove(tag, "1.0", "end")
            except Exception:
                pass

    def _style_to_tag(self, style: str) -> str:
        return {
            "bold": "fmt_bold",
            "italic": "fmt_italic",
            "underline": "fmt_underline",
            "strike": "fmt_strike"
        }.get(style, "fmt_bold")

    def get_format_meta_json(self) -> str:
        return json.dumps(self.format_meta, ensure_ascii=False)


# ---------------- NotesUI ----------------
class NotesUI:
    def __init__(self, master, notes_service):
        self.master = master
        self.notes_service = notes_service
        self.frame = ttk.Frame(master)

        control = ttk.Frame(self.frame)
        control.pack(fill="x", padx=8, pady=8)

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

        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill="both", expand=True, padx=8, pady=6)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "title", "tags", "created_at"),
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
        self.tree.heading("title", text="Заголовок")
        self.tree.heading("tags", text="Теги")
        self.tree.heading("created_at", text="Создано")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("title", width=360, anchor="w")
        self.tree.column("tags", width=180, anchor="w")
        self.tree.column("created_at", width=160, anchor="center")

        self.tree.bind("<Double-1>", self._on_double_click)

        bottom = ttk.Frame(self.frame)
        bottom.pack(fill="x", padx=8, pady=8)

        ttk.Button(bottom, text="Удалить", command=self.delete_note).pack(side="left")
        ttk.Button(bottom, text="Просмотр", command=self.view_note).pack(side="left", padx=6)
        ttk.Button(bottom, text="Редактировать", command=self.edit_note).pack(side="left", padx=6)

        self.load_notes()

    def get_frame(self):
        return self.frame

    # ---------------- CRUD и поиск ----------------
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
            self.title_entry.focus_set()
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
            if not results:
                messagebox.showinfo("Поиск", "Ничего не найдено")
                return
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
        if messagebox.askyesno("Подтвердите", "Удалить выбранную заметку?"):
            try:
                self.notes_service.delete_note(note_id)
                self.load_notes()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def view_note(self):
        sel = self.tree.selection()
        if not sel:
            self.tree.showwarning("Ошибка", "Выберите заметку для просмотра")
            return
        note_id = self.tree.item(sel[0])["values"][0]
        try:
            note = self.notes_service.get_note_by_id(note_id)
            if not note:
                messagebox.showerror("Ошибка", "Заметка не найдена")
                return
            if len(note) == 6:
                _, title, content, tags, created_at, _ = note
            else:
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
            messagebox.showerror("Ошибка", "Заметка не найдена")
            return

        if len(note) == 6:
            _, title, content, tags, created_at, format_meta = note
        else:
            _, title, content, tags, created_at = note
            format_meta = "{}"

        try:
            original_meta = json.loads(format_meta or "{}")
        except Exception:
            original_meta = {}
        working_meta = json.loads(json.dumps(original_meta))

        win = tk.Toplevel(self.master)
        win.title("Редактировать заметку")
        win.geometry("920x560")
        win.transient(self.master)

        container = ttk.Frame(win)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        editor_frame = ttk.Frame(container)
        editor_frame.pack(side="left", fill="both", expand=True)

        top_fields = ttk.Frame(editor_frame)
        top_fields.pack(fill="x", padx=4, pady=(0, 6))

        ttk.Label(top_fields, text="Заголовок:").grid(row=0, column=0, sticky="w")
        title_entry = ttk.Entry(top_fields)
        title_entry.grid(row=0, column=1, sticky="ew", padx=8)
        title_entry.insert(0, title or "")
        top_fields.columnconfigure(1, weight=1)

        ttk.Label(top_fields, text="Теги:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        tags_entry = ttk.Entry(top_fields)
        tags_entry.grid(row=1, column=1, sticky="ew", padx=8, pady=(6, 0))
        tags_entry.insert(0, tags or "")

        content_frame = ttk.Frame(editor_frame)
        content_frame.pack(fill="both", expand=True, padx=4, pady=4)

        text_area = tk.Text(content_frame, wrap="word")
        text_area.pack(side="left", fill="both", expand=True)
        text_area.insert("1.0", content or "")

        text_vsb = ttk.Scrollbar(content_frame, orient="vertical", command=text_area.yview)
        text_vsb.pack(side="right", fill="y")
        text_area.configure(yscrollcommand=text_vsb.set)

        # панель форматирования — полноценное окно, скрыто по умолчанию
        panel = FormattingPanel(win, text_area, working_meta)

        footer = ttk.Frame(win)
        footer.pack(fill="x", padx=12, pady=(6, 10))

        left_box = ttk.Frame(footer)
        left_box.pack(side="left")

        def toggle_panel():
            try:
                if panel.state() == "normal":
                    panel.hide()
                else:
                    panel.show()
            except Exception:
                panel.show()

        ttk.Button(left_box, text="Редакт.", command=toggle_panel).pack(side="left")

        def export_md():
            path = filedialog.asksaveasfilename(title="Сохранить как Markdown", defaultextension=".md",
                                                filetypes=[("Markdown", "*.md"), ("Все файлы", "*.*")])
            if not path:
                return
            try:
                cur_title = title_entry.get().strip()
                cur_tags = tags_entry.get().strip()
                cur_content = text_area.get("1.0", "end-1c")
                self.notes_service.update_note(
                    note_id, cur_title, cur_content, cur_tags, panel.get_format_meta_json()
                )
                self.notes_service.export_note_md(note_id, path)
                messagebox.showinfo("Экспорт", f"Сохранено: {path}")
            except Exception as e:
                messagebox.showerror("Экспорт", f"Ошибка: {e}")

        def export_html():
            path = filedialog.asksaveasfilename(title="Сохранить как HTML", defaultextension=".html",
                                                filetypes=[("HTML", "*.html"), ("Все файлы", "*.*")])
            if not path:
                return
            try:
                cur_title = title_entry.get().strip()
                cur_tags = tags_entry.get().strip()
                cur_content = text_area.get("1.0", "end-1c")
                self.notes_service.update_note(
                    note_id, cur_title, cur_content, cur_tags, panel.get_format_meta_json()
                )
                self.notes_service.export_note_html(note_id, path)
                messagebox.showinfo("Экспорт", f"Сохранено: {path}")
            except Exception as e:
                messagebox.showerror("Экспорт", f"Ошибка: {e}")

        ttk.Button(left_box, text="Экспорт MD", command=export_md).pack(side="left", padx=(8, 8))
        ttk.Button(left_box, text="Экспорт HTML", command=export_html).pack(side="left")

        right_box = ttk.Frame(footer)
        right_box.pack(side="right")

        def save_and_close():
            new_title = title_entry.get().strip()
            new_tags = tags_entry.get().strip()
            new_content = text_area.get("1.0", "end-1c")
            if not new_title:
                messagebox.showwarning("Ошибка", "Заголовок не может быть пустым")
                return
            try:
                self.notes_service.update_note(
                    note_id, new_title, new_content, new_tags, panel.get_format_meta_json()
                )
                try:
                    panel.destroy()
                except Exception:
                    pass
                self.load_notes()
                win.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        def cancel_and_close():
            try:
                panel.destroy()
            except Exception:
                pass
            win.destroy()

        ttk.Button(right_box, text="Сохранить", command=save_and_close).pack(side="right", padx=6)
        ttk.Button(right_box, text="Отмена", command=cancel_and_close).pack(side="right")

        panel._apply_all_meta_tags()
        title_entry.focus_set()

    def _on_double_click(self, event):
        sel = self.tree.identify_row(event.y)
        if sel:
            self.tree.selection_set(sel)
            self.edit_note()
