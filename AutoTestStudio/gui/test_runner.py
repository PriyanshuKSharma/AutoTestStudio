import subprocess
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog
from database.sqlite import get_db
from datetime import datetime


class TestRunnerPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._script_path = ""
        self._process = None
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(top, text="Test Runner", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        self._stop_btn = ctk.CTkButton(top, text="Stop", width=80, command=self._stop, state="disabled", fg_color="red")
        self._stop_btn.pack(side="right", padx=4)
        self._run_btn = ctk.CTkButton(top, text="▶ Run", width=80, command=self._run, fg_color="green")
        self._run_btn.pack(side="right", padx=4)

        sel_row = ctk.CTkFrame(self, fg_color="transparent")
        sel_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(sel_row, text="Script:").pack(side="left")
        self._path_label = ctk.CTkLabel(sel_row, text="None selected", text_color="gray")
        self._path_label.pack(side="left", padx=8)
        ctk.CTkButton(sel_row, text="Browse", width=80, command=self._browse).pack(side="left")

        self._status_label = ctk.CTkLabel(self, text="Idle", text_color="gray")
        self._status_label.pack(anchor="w", padx=16)

        self._output = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Courier", size=12), state="disabled")
        self._output.pack(fill="both", expand=True, padx=16, pady=8)

        # Results table
        ctk.CTkLabel(self, text="Recent Results", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16)
        self._results_frame = ctk.CTkScrollableFrame(self, height=140)
        self._results_frame.pack(fill="x", padx=16, pady=(0, 8))
        self._load_results()

    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[("Python", "*.py"), ("All", "*.*")])
        if path:
            self._script_path = path
            self._path_label.configure(text=path)

    def _run(self):
        if not self._script_path:
            return
        self._clear_output()
        self._run_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._status_label.configure(text="Running…", text_color="yellow")
        threading.Thread(target=self._exec, daemon=True).start()

    def _exec(self):
        try:
            self._process = subprocess.Popen(
                [sys.executable, self._script_path],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            for line in self._process.stdout:
                self.after(0, self._append_output, line)
            self._process.wait()
            rc = self._process.returncode
            self.after(0, self._on_done, rc)
        except Exception as e:
            self.after(0, self._append_output, f"Error: {e}\n")
            self.after(0, self._on_done, -1)

    def _stop(self):
        if self._process:
            self._process.terminate()

    def _on_done(self, rc: int):
        self._run_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        if rc == 0:
            self._status_label.configure(text="✓ Passed", text_color="green")
        else:
            self._status_label.configure(text=f"✗ Failed (exit {rc})", text_color="red")
        self._load_results()

    def _append_output(self, text: str):
        self._output.configure(state="normal")
        self._output.insert("end", text)
        self._output.see("end")
        self._output.configure(state="disabled")

    def _clear_output(self):
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.configure(state="disabled")

    def _load_results(self):
        for w in self._results_frame.winfo_children():
            w.destroy()
        db = get_db()
        rows = db.execute("SELECT timestamp, test_name, status FROM test_results ORDER BY id DESC LIMIT 20").fetchall()
        for r in rows:
            row_frame = ctk.CTkFrame(self._results_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            color = "green" if r["status"] == "PASS" else "red"
            ctk.CTkLabel(row_frame, text=r["status"], width=60, text_color=color,
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=8)
            ctk.CTkLabel(row_frame, text=r["test_name"], width=200, anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=r["timestamp"][:19], text_color="gray").pack(side="left", padx=8)
