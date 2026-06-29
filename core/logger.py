import json
from datetime import datetime
from database.sqlite import get_db


class EventLogger:
    def log(self, event_type: str, severity: str, message: str, signals: dict = None):
        db = get_db()
        db.execute(
            "INSERT INTO events (timestamp, event_type, severity, message, signals) VALUES (?,?,?,?,?)",
            (
                datetime.utcnow().isoformat(),
                event_type,
                severity,
                message,
                json.dumps(signals or {}),
            ),
        )
        db.commit()

    def get_recent(self, limit: int = 100):
        db = get_db()
        rows = db.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def fault(self, message: str, signals: dict = None):
        self.log("fault", "critical", message, signals)

    def info(self, message: str, signals: dict = None):
        self.log("info", "info", message, signals)


logger = EventLogger()
