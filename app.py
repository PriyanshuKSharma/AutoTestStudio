import sys
import os


def _base_dir() -> str:
    """Return the correct base directory whether running as script or frozen exe."""
    if getattr(sys, "frozen", False):
        # PyInstaller extracts everything to sys._MEIPASS at runtime
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _base_dir()
sys.path.insert(0, BASE_DIR)

# Keep the DB and project.json next to the exe / script, not inside _MEIPASS
RUNTIME_DIR = (
    os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else BASE_DIR
)
os.chdir(RUNTIME_DIR)

from database.sqlite import get_db  # noqa: E402
from core.project import project  # noqa: E402
from gui.main_window import MainWindow  # noqa: E402


def main():
    project.load()
    get_db()
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
