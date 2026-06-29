import cantools
from typing import Optional


class DBCManager:
    def __init__(self):
        self._db: Optional[cantools.db.Database] = None
        self.path: Optional[str] = None

    def load(self, path: str):
        self._db = cantools.db.load_file(path)
        self.path = path

    def messages(self):
        if not self._db:
            return []
        return self._db.messages

    def decode(self, can_id: int, data: bytes) -> Optional[dict]:
        if not self._db:
            return None
        try:
            msg = self._db.get_message_by_frame_id(can_id)
            return msg.decode(data)
        except Exception:
            return None

    def encode(self, name: str, signals: dict) -> bytes:
        if not self._db:
            raise RuntimeError("No DBC loaded")
        msg = self._db.get_message_by_name(name)
        return msg.encode(signals)

    def get_message(self, can_id: int):
        if not self._db:
            return None
        try:
            return self._db.get_message_by_frame_id(can_id)
        except Exception:
            return None

    @property
    def loaded(self) -> bool:
        return self._db is not None


dbc_manager = DBCManager()
