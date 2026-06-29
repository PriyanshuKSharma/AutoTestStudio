import sys
import os

# Ensure AutoTestStudio root is on the path so all imports resolve
sys.path.insert(0, os.path.dirname(__file__))

from database.sqlite import get_db   # initialise DB on startup
from core.project import project
from gui.main_window import MainWindow


def main():
    project.load()
    get_db()          # creates tables if they don't exist
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
