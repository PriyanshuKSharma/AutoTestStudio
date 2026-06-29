from core.bus import bus_manager


def connect(channel: str = "vcan0") -> bool:
    return bus_manager.connect(interface="virtual", channel=channel)
