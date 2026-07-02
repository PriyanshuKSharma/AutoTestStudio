import threading
from typing import Callable


class Scheduler:
    def __init__(self):
        self._tasks: list[dict] = []

    def add(self, fn: Callable, interval_ms: int):
        entry = {
            "fn": fn,
            "interval": interval_ms / 1000.0,
            "timer": None,
            "running": False,
        }
        self._tasks.append(entry)
        return entry

    def _run(self, entry: dict):
        if not entry["running"]:
            return
        try:
            entry["fn"]()
        except Exception:
            pass
        t = threading.Timer(entry["interval"], self._run, args=(entry,))
        t.daemon = True
        t.start()
        entry["timer"] = t

    def start_all(self):
        for entry in self._tasks:
            entry["running"] = True
            self._run(entry)

    def stop_all(self):
        for entry in self._tasks:
            entry["running"] = False
            if entry["timer"]:
                entry["timer"].cancel()


scheduler = Scheduler()
