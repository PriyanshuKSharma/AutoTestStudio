import can
from typing import Callable, Optional


class BusManager:
    def __init__(self):
        self._bus: Optional[can.Bus] = None
        self._notifier: Optional[can.Notifier] = None
        self.interface = "virtual"
        self.channel = "vcan0"
        self.bitrate = 500000

    def connect(self, interface: str, channel: str, bitrate: int = 500000) -> bool:
        self.disconnect()
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        try:
            self._bus = can.Bus(interface=interface, channel=channel, bitrate=bitrate)
            return True
        except Exception as e:
            self._bus = None
            raise ConnectionError(f"Bus connect failed: {e}")

    def disconnect(self):
        if self._notifier:
            self._notifier.stop()
            self._notifier = None
        if self._bus:
            self._bus.shutdown()
            self._bus = None

    def send(self, msg: can.Message):
        if not self._bus:
            raise RuntimeError("Bus not connected")
        self._bus.send(msg)

    def add_listener(self, callback: Callable[[can.Message], None]):
        if not self._bus:
            raise RuntimeError("Bus not connected")
        listener = can.BufferedReader()
        listener.on_message_received = callback
        self._notifier = can.Notifier(self._bus, [listener])

    def recv(self, timeout: float = 1.0) -> Optional[can.Message]:
        if not self._bus:
            return None
        return self._bus.recv(timeout=timeout)

    @property
    def connected(self) -> bool:
        return self._bus is not None


bus_manager = BusManager()
