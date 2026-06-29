"""
Vector XL / Peak / SocketCAN plugin stub.
Swap interface string for real hardware: 'vector', 'pcan', 'socketcan'.
"""
from core.bus import bus_manager


def connect(channel: str = "PCAN_USBBUS1", interface: str = "pcan", bitrate: int = 500000) -> bool:
    return bus_manager.connect(interface=interface, channel=channel, bitrate=bitrate)
