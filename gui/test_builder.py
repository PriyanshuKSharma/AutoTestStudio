import customtkinter as ctk
from tkinter import filedialog

TEMPLATE = '''"""
AutoTest Studio test script.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import can
from framework.decorators import on_start, on_stop, on_message, every
from framework.testcase import TestCase
from core.bus import bus_manager
from core.logger import logger

tc = TestCase("My_Test")


@on_start
def initialize():
    bus_manager.connect(interface="virtual", channel="vcan0")


@on_stop
def cleanup():
    bus_manager.disconnect()


@on_message(0x100)
def handle_status(msg: can.Message):
    soc = msg.data[0] * 0.5
    tc.expect_in_range(soc, 0, 100, "SOC")


@every(100)
def heartbeat():
    pass
'''


class TestBuilderPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._current_path = None
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
            text="Test Builder",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w",
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Create, edit, and maintain Python automated test scripts",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
            anchor="w",
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # Toolbar Actions
        actions_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_row.grid(row=0, column=1, sticky="e")

        self.btn_new = ctk.CTkButton(
            actions_row,
            text="New Script",
            width=90,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._new,
        )
        self.btn_new.pack(side="left", padx=4)

        self.btn_open = ctk.CTkButton(
            actions_row,
            text="Open File",
            width=90,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._open,
        )
        self.btn_open.pack(side="left", padx=4)

        self.btn_save_as = ctk.CTkButton(
            actions_row,
            text="Save As",
            width=80,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._save_as,
        )
        self.btn_save_as.pack(side="right", padx=4)

        self.btn_save = ctk.CTkButton(
            actions_row,
            text="Save",
            width=80,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#1f538d", "#60a5fa"),
            command=self._save,
        )
        self.btn_save.pack(side="right", padx=4)

        # ─── EDITOR CARD CONTAINER ───
        editor_card = ctk.CTkFrame(
            self,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12,
        )
        editor_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Path metadata header
        path_header = ctk.CTkFrame(
            editor_card, fg_color=("gray95", "gray25"), height=36, corner_radius=10
        )
        path_header.pack(fill="x", padx=12, pady=(12, 4))
        path_header.pack_propagate(False)

        ctk.CTkLabel(
            path_header,
            text="Active File:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
        ).pack(side="left", padx=12)

        self._path_label = ctk.CTkLabel(
            path_header,
            text="Untitled Script",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=("gray40", "gray60"),
        )
        self._path_label.pack(side="left", padx=(4, 12))

        # Code Textbox Editor
        self._editor = ctk.CTkTextbox(
            editor_card,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color="transparent",
        )
        self._editor.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._editor.insert("end", TEMPLATE)

    def _new(self):
        self._editor.delete("1.0", "end")
        self._editor.insert("end", TEMPLATE)
        self._current_path = None
        self._path_label.configure(text="Untitled Script")

    def _open(self):
        path = filedialog.askopenfilename(
            filetypes=[("Python", "*.py"), ("All", "*.*")]
        )
        if not path:
            return
        with open(path) as f:
            content = f.read()
        self._editor.delete("1.0", "end")
        self._editor.insert("end", content)
        self._current_path = path
        self._path_label.configure(text=path)

    def _save(self):
        if not self._current_path:
            self._save_as()
            return
        with open(self._current_path, "w") as f:
            f.write(self._editor.get("1.0", "end"))

    def _save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".py", filetypes=[("Python", "*.py")]
        )
        if not path:
            return
        self._current_path = path
        self._path_label.configure(text=path)
        self._save()

    def get_script_path(self) -> str:
        return self._current_path or ""

    def get_script_content(self) -> str:
        return self._editor.get("1.0", "end")
