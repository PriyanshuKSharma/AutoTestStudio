# -*- mode: python ; coding: utf-8 -*-
"""
AutoTest Studio — PyInstaller build spec
Run:  pyinstaller AutoTestStudio.spec --noconfirm --clean
Out:  dist\AutoTestStudio\AutoTestStudio.exe
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

ROOT = os.path.abspath(".")

# ── Hidden imports ────────────────────────────────────────────────────────────
hidden = [
    *collect_submodules("customtkinter"),
    *collect_submodules("cantools"),
    "can.interfaces.virtual",
    "can.interfaces.socketcan",
    "can.interfaces.pcan",
    "can.interfaces.vector",
    "can.interfaces.kvaser",
    "can.interfaces.usb2can",
    "can.interfaces.serial",
    "keyring.backends.Windows",
    "keyring.backends.SecretService",
    "keyring.backends.fail",
    "keyring.core",
    "git",
    "gitdb",
    "smmap",
    "sqlite3",
    "tkinter",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "_tkinter",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
]

# ── Data files ────────────────────────────────────────────────────────────────
datas = [
    *collect_data_files("customtkinter"),   # theme JSON + images
    *collect_data_files("cantools"),        # grammar files
    (os.path.join(ROOT, "assets"),  "assets"),   # bms.dbc + icon
    (os.path.join(ROOT, "tests"),   "tests"),    # example test scripts
    (os.path.join(ROOT, "docs"),    "docs"),     # documentation
    (os.path.join(ROOT, "README.md"), "."),
]

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [os.path.join(ROOT, "app.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "numpy", "pandas", "scipy",
        "PyQt5", "PyQt6", "PySide2", "PySide6",
        "wx",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutoTestStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX can corrupt some Windows DLLs — keep off
    console=False,      # no black console window behind the GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT, "assets", "icon.ico")
         if os.path.exists(os.path.join(ROOT, "assets", "icon.ico")) else None,
    version="version_info.txt",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AutoTestStudio",
)
