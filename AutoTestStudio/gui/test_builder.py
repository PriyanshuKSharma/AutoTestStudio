import customtkinter as ctk
from tkinter import filedialog
import os

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
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(top, text="Test Builder", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="Save", width=80, command=self._save).pack(side="right", padx=4)
        ctk.CTkButton(top, text="Save As", width=80, command=self._save_as).pack(side="right", padx=4)
        ctk.CTkButton(top, text="Open", width=80, command=self._open).pack(side="right", padx=4)
        ctk.CTkButton(top, text="New", width=80, command=self._new).pack(side="right", padx=4)

        self._path_label = ctk.CTkLabel(self, text="Unsaved", text_color="gray")
        self._path_label.pack(anchor="w", padx=16)

        self._editor = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Courier", size=13))
        self._editor.pack(fill="both", expand=True, padx=16, pady=8)
        self._editor.insert("end", TEMPLATE)

    def _new(self):
        self._editor.delete("1.0", "end")
        self._editor.insert("end", TEMPLATE)
        self._current_path = None
        self._path_label.configure(text="Unsaved")

    def _open(self):
        path = filedialog.askopenfilename(filetypes=[("Python", "*.py"), ("All", "*.*")])
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
        path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python", "*.py")])
        if not path:
            return
        self._current_path = path
        self._path_label.configure(text=path)
        self._save()

    def get_script_path(self) -> str:
        return self._current_path or ""

    def get_script_content(self) -> str:
        return self._editor.get("1.0", "end")
