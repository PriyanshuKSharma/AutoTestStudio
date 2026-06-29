from datetime import datetime
from database.sqlite import get_db


class TestCase:
    def __init__(self, name: str):
        self.name = name
        self._steps: list[dict] = []
        self._passed = 0
        self._failed = 0

    def check(self, condition: bool, description: str):
        status = "PASS" if condition else "FAIL"
        self._steps.append({"description": description, "status": status})
        if condition:
            self._passed += 1
        else:
            self._failed += 1
        return condition

    def expect_equal(self, actual, expected, label: str = ""):
        desc = f"{label}: expected {expected}, got {actual}"
        return self.check(actual == expected, desc)

    def expect_in_range(self, value, low, high, label: str = ""):
        desc = f"{label}: {value} in [{low}, {high}]"
        return self.check(low <= value <= high, desc)

    @property
    def passed(self) -> bool:
        return self._failed == 0

    def summary(self) -> dict:
        return {
            "name": self.name,
            "passed": self._passed,
            "failed": self._failed,
            "steps": self._steps,
            "result": "PASS" if self.passed else "FAIL",
        }

    def save(self):
        import json
        db = get_db()
        s = self.summary()
        db.execute(
            "INSERT INTO test_results (timestamp, test_name, status, details) VALUES (?,?,?,?)",
            (datetime.utcnow().isoformat(), self.name, s["result"], json.dumps(s["steps"])),
        )
        db.commit()
