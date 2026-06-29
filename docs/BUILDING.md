# Building AutoTest Studio as a Windows Application

This document explains how to go from Python source code to a professional
Windows installer — a single `.exe` setup file that installs the app exactly
like TestBench, Visual Studio, or any other Windows desktop application.

---

## What You Get

After running the build:

```
AutoTestStudio_Setup_v0.1.0.exe        ← single installer, ship this
dist\
  AutoTestStudio\
    AutoTestStudio.exe                  ← standalone app, no Python needed
    _internal\                          ← all bundled deps (auto-generated)
```

When a user runs the installer on any Windows machine:

```
Setup Wizard
  ↓
Welcome screen
  ↓
License agreement
  ↓
Choose install directory  (default: C:\Program Files\AutoTest Studio)
  ↓
Choose components
  ✓ Core Application   (required)
  ✓ Desktop Shortcut
  ✓ Start Menu Entry
  ↓
Installing files...
  ↓
Launch AutoTest Studio  ✓
```

The installed app appears in:
- **Start Menu** → AutoTest Studio
- **Desktop** shortcut
- **Add or Remove Programs** (with proper uninstaller)

---

## Prerequisites

Install these once on your Windows build machine.

### 1. Python 3.10+

Download from https://python.org

During install, tick **"Add Python to PATH"**.

### 2. NSIS 3.x

Download from https://nsis.sourceforge.io/Download

Install with default options. This is what creates the setup wizard `.exe`.

---

## Build Steps

### Option A — One click

```bat
build.bat
```

That is it. The script does everything:
1. Creates a Python virtual environment
2. Installs all dependencies
3. Runs PyInstaller to bundle the app
4. Runs NSIS to wrap it into an installer
5. Outputs `AutoTestStudio_Setup_v0.1.0.exe`

---

### Option B — Manual steps

**Step 1 — Set up environment**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Step 2 — Generate icon (first time only)**

```bat
python installer\make_icon.py
```

**Step 3 — Bundle with PyInstaller**

```bat
pyinstaller AutoTestStudio.spec --noconfirm --clean
```

Output: `dist\AutoTestStudio\AutoTestStudio.exe`

Test it before building the installer:

```bat
dist\AutoTestStudio\AutoTestStudio.exe
```

**Step 4 — Build the installer with NSIS**

```bat
"C:\Program Files (x86)\NSIS\makensis.exe" installer\AutoTestStudio.nsi
```

Output: `AutoTestStudio_Setup_v0.1.0.exe`

---

## File Structure

```
canoe_simulator_mqi\
├── app.py                      Entry point (frozen-path aware)
├── AutoTestStudio.spec         PyInstaller bundle config
├── version_info.txt            Windows exe version metadata
├── build.bat                   One-click full build
├── run_local.bat               Run from source (development)
├── requirements.txt            Python dependencies
├── LICENSE.txt                 License shown in setup wizard
│
├── assets\
│   ├── bms.dbc                 Bundled with the exe
│   └── icon.ico                App icon (all sizes)
│
└── installer\
    ├── AutoTestStudio.nsi      NSIS installer script
    └── make_icon.py            Icon generator (run once)
```

---

## How It Works Internally

### PyInstaller

PyInstaller analyzes all imports in `app.py`, follows every `import` statement
recursively, and copies:

- All `.py` files compiled to `.pyc`
- All DLLs and `.pyd` extension modules
- All data files declared in the spec (`customtkinter` themes, `bms.dbc`, etc.)

Into `dist\AutoTestStudio\`. The result runs on any Windows machine with no
Python installed because the Python interpreter itself is bundled inside.

The spec file (`AutoTestStudio.spec`) controls exactly what gets included.

### NSIS

NSIS takes the entire `dist\AutoTestStudio\` folder and compresses it into a
single self-extracting `.exe` with a setup wizard. When the user runs it:

1. Files are extracted to the chosen install directory
2. Registry keys are written for Add/Remove Programs
3. Shortcuts are created on Desktop and Start Menu
4. An uninstaller is registered

---

## Customising the Installer

### Change install location default

In `installer\AutoTestStudio.nsi`, edit:

```nsi
!define INSTALL_DIR "$PROGRAMFILES64\AutoTest Studio"
```

### Change version number

Update in three places:
- `config.py` → `VERSION = "0.2.0"`
- `version_info.txt` → `filevers=(0, 2, 0, 0)` and all version strings
- `installer\AutoTestStudio.nsi` → `!define APP_VERSION "0.2.0"`

### Replace the icon

Drop a 256×256 `.ico` file at `assets\icon.ico` and rebuild.
Use https://convertico.com to convert a PNG to ICO with all required sizes.

### Add new files to the bundle

In `AutoTestStudio.spec`, add to the `datas` list:

```python
(os.path.join(ROOT, "my_folder"), "my_folder"),
```

---

## Troubleshooting

### "Module not found" when running the exe

Add the module to `hiddenimports` in `AutoTestStudio.spec`:

```python
hidden = [
    ...
    "my.missing.module",
]
```

### customtkinter theme not loading

`collect_data_files("customtkinter")` in the spec handles this. If it breaks,
verify the line is present in the spec `datas` list.

### NSIS "can't find file" error

Make sure PyInstaller ran successfully first and `dist\AutoTestStudio\` exists
before running NSIS.

### App crashes immediately with no window

Set `console=True` in `AutoTestStudio.spec` temporarily, rebuild, and run from
a terminal to see the traceback.
