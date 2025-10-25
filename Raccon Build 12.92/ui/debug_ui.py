# ui/debug_ui.py
import tkinter as tk
from tkinter import ttk
import sys, logging, queue, time, os, datetime, io

class _StreamProxy:
    def __init__(self, q, name):
        self.q = q
        self.name = name
    def write(self, data):
        if data:
            self.q.put((self.name, str(data)))
    def flush(self):
        pass

class _QueueLoggingHandler(logging.Handler):
    def __init__(self, q):
        super().__init__()
        self.q = q
    def emit(self, record):
        try:
            msg = self.format(record)
            self.q.put(("log", msg))
        except Exception:
            pass

class DebugUI:
    def __init__(self, master, autostart=False):
        self.win = tk.Toplevel(master)
        self.win.title("Debugger")
        self.win.geometry("880x520")

        self.output = tk.Text(self.win, wrap="word", state="disabled", bg="black", fg="lime")
        self.output.pack(fill="both", expand=True, padx=6, pady=6)

        ctrl = ttk.Frame(self.win); ctrl.pack(fill="x", padx=6, pady=(0,6))
        self.start_btn = ttk.Button(ctrl, text="▶ Старт", command=self.start); self.start_btn.pack(side="left", padx=4)
        self.stop_btn = ttk.Button(ctrl, text="⏹ Стоп", command=self.stop); self.stop_btn.pack(side="left", padx=4)
        self.save_btn  = ttk.Button(ctrl, text="💾 Сохранить", command=self.save); self.save_btn.pack(side="left", padx=4)
        self.mode_var = tk.StringVar(value="all")
        ttk.Radiobutton(ctrl, text="All", variable=self.mode_var, value="all").pack(side="left", padx=6)
        ttk.Radiobutton(ctrl, text="Errors only", variable=self.mode_var, value="errors").pack(side="left")

        # очередь и буфер
        self.q = queue.Queue()
        self.buffer = io.StringIO()

        # сохранить оригиналы
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        self._orig_handlers = logging.getLogger().handlers[:]

        # logging handler
        self._log_handler = _QueueLoggingHandler(self.q)
        self._log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))

        # флаг активности
        self.active = False

        # запуск поллинга
        self._poll()

        if autostart:
            self.start()

    def _append(self, line: str):
        self.output.configure(state="normal")
        self.output.insert("end", line + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _poll(self):
        try:
            while True:
                src, data = self.q.get_nowait()
                for ln in str(data).splitlines():
                    if not ln:
                        continue
                    ts = time.strftime("[%H:%M:%S]")
                    if self.mode_var.get() == "errors":
                        if src == "log":
                            if "WARNING" in ln or "ERROR" in ln or "CRITICAL" in ln:
                                pass
                            else:
                                continue
                        elif src == "stderr":
                            pass
                        else:
                            continue
                    out = f"{ts} [{src}] {ln}"
                    self.buffer.write(out + "\n")
                    self._append(out)
        except queue.Empty:
            pass
        self.win.after(120, self._poll)

    def start(self):
        if self.active:
            self._append("[DEBUG] already started")
            return
        sys.stdout = _StreamProxy(self.q, "stdout")
        sys.stderr = _StreamProxy(self.q, "stderr")
        root_logger = logging.getLogger()
        root_logger.handlers = [self._log_handler]
        root_logger.setLevel(logging.DEBUG)
        self.active = True
        self._append("[DEBUG] started")

    def stop(self):
        if not self.active:
            self._append("[DEBUG] not active")
            return
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr
        logging.getLogger().handlers = self._orig_handlers
        self.active = False
        self._append("[DEBUG] stopped")

    def save(self, path: str = None):
        if path is None:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f"debug_log_{ts}.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.buffer.getvalue())
            self._append(f"[DEBUG] saved to {path}")
        except Exception as e:
            self._append(f"[DEBUG] save error: {e}")

    # совместимость с write/flush
    def write(self, data):
        if data:
            self.q.put(("custom", str(data)))
    def flush(self):
        pass
