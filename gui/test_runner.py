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
        # ─── HEADER ───
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 12))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            title_frame,
            text="Test Runner",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Execute scripts, monitor test assertions, and view history logs",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
            anchor="w"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # ─── CONTROLS CARD ───
        ctrl_card = ctk.CTkFrame(
            self,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        ctrl_card.pack(fill="x", padx=24, pady=(0, 16))

        ctrl_inner = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        ctrl_inner.pack(padx=20, pady=16, fill="both", expand=True)
        ctrl_inner.columnconfigure(1, weight=1)

        # Script Row
        ctk.CTkLabel(
            ctrl_inner,
            text="Script File:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        self._path_label = ctk.CTkLabel(
            ctrl_inner,
            text="No script selected",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=("gray50", "gray40"),
            anchor="w"
        )
        self._path_label.grid(row=0, column=1, sticky="ew")

        # Action Buttons on right
        btn_frame = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        btn_frame.grid(row=0, column=2, sticky="e", padx=(12, 0))

        self.btn_browse = ctk.CTkButton(
            btn_frame,
            text="Browse",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._browse,
            width=80,
            height=32
        )
        self.btn_browse.pack(side="left", padx=4)

        self._run_btn = ctk.CTkButton(
            btn_frame,
            text="Run Test",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#10b981", "#10b981"),
            hover_color=("#059669", "#059669"),
            command=self._run,
            width=80,
            height=32
        )
        self._run_btn.pack(side="left", padx=4)

        self._stop_btn = ctk.CTkButton(
            btn_frame,
            text="Stop",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._stop,
            state="disabled",
            width=80,
            height=32
        )
        self._stop_btn.pack(side="left", padx=4)

        # Status sub-row
        status_bar = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        status_bar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        self.status_title_lbl = ctk.CTkLabel(
            status_bar,
            text="Execution Status: ",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray50", "gray40")
        )
        self.status_title_lbl.pack(side="left")

        self._status_label = ctk.CTkLabel(
            status_bar,
            text="Idle",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("gray40", "gray60")
        )
        self._status_label.pack(side="left")

        # ─── CONSOLE OUTPUT CARD ───
        console_card = ctk.CTkFrame(
            self,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        console_card.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        console_inner = ctk.CTkFrame(console_card, fg_color="transparent")
        console_inner.pack(padx=16, pady=12, fill="both", expand=True)

        ctk.CTkLabel(
            console_inner,
            text="CONSOLE LOG OUTPUT",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 6))

        self._output = ctk.CTkTextbox(
            console_inner,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=("gray95", "gray17"),
            border_width=1,
            border_color=("gray80", "gray30"),
            corner_radius=6,
            state="disabled"
        )
        self._output.pack(fill="both", expand=True)

        # ─── RECENT RESULTS CARD ───
        results_card = ctk.CTkFrame(
            self,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        results_card.pack(fill="x", padx=24, pady=(0, 20))

        results_inner = ctk.CTkFrame(results_card, fg_color="transparent")
        results_inner.pack(padx=16, pady=12, fill="both", expand=True)

        ctk.CTkLabel(
            results_inner,
            text="RECENT RESULTS HISTORY",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 6))

        self._results_frame = ctk.CTkScrollableFrame(results_inner, height=130, fg_color="transparent")
        self._results_frame.pack(fill="x", expand=True)
        
        self._load_results()

    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[("Python", "*.py"), ("All", "*.*")])
        if path:
            self._script_path = path
            self._path_label.configure(text=path, text_color=("black", "white"))

    def _run(self):
        if not self._script_path:
            return
        self._clear_output()
        self._run_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal", fg_color="#dc2626", hover_color="#ef4444")
        self._status_label.configure(text="Running...", text_color="#f59e0b")
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
        self._stop_btn.configure(state="disabled", fg_color=None, hover_color=None)
        if rc == 0:
            self._status_label.configure(text="[PASSED] Script finished successfully.", text_color="#10b981")
        else:
            self._status_label.configure(text=f"[FAILED] Script failed (exit code {rc}).", text_color="#ef4444")
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
        
        self._results_frame.columnconfigure(0, weight=1)
        self._results_frame.columnconfigure(1, weight=3)
        self._results_frame.columnconfigure(2, weight=2)

        db = get_db()
        rows = db.execute("SELECT timestamp, test_name, status FROM test_results ORDER BY id DESC LIMIT 20").fetchall()
        for idx, r in enumerate(rows):
            row_bg = ("gray95", "gray24") if idx % 2 == 0 else "transparent"
            row_frame = ctk.CTkFrame(self._results_frame, fg_color=row_bg, corner_radius=4)
            row_frame.pack(fill="x", pady=1, padx=4)
            
            status_text = f"[{r['status']}]"
            color = "#10b981" if r["status"] == "PASS" else "#ef4444"
            
            lbl_status = ctk.CTkLabel(
                row_frame,
                text=status_text,
                width=80,
                text_color=color,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                anchor="w"
            )
            lbl_status.pack(side="left", padx=12, pady=4)

            lbl_name = ctk.CTkLabel(
                row_frame,
                text=r["test_name"],
                font=ctk.CTkFont(family="Segoe UI", size=12),
                anchor="w"
            )
            lbl_name.pack(side="left", fill="x", expand=True, padx=4, pady=4)

            lbl_time = ctk.CTkLabel(
                row_frame,
                text=r["timestamp"][:19],
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color=("gray50", "gray40"),
                anchor="e"
            )
            lbl_time.pack(side="right", padx=12, pady=4)
