"""
BMS Simulator
Generates realistic BMS CAN frames on the virtual bus at 100 ms intervals.
Enable from the CAN Monitor panel to produce live traffic without real hardware.
"""
import threading
import math
import time
import can
from core.bus import bus_manager


class BMSSimulator:
    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None
        self._tick = 0

    def start(self):
        if self._running:
            return
        self._running = True
        self._tick = 0
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def _loop(self):
        while self._running:
            try:
                if bus_manager.connected:
                    self._send_status()
                    self._send_pack_vals()
                    self._send_temps()
                    self._tick += 1
            except Exception:
                pass
            time.sleep(0.1)

    # ------------------------------------------------------------------ #
    #  Frame builders — raw byte encoding, no DBC dependency              #
    # ------------------------------------------------------------------ #
    def _send_status(self):
        # SOC 20-100 % cycling slowly, scale 0.5 → raw = soc/0.5
        soc_pct = 20 + ((self._tick // 20) % 80)
        soc_raw = int(soc_pct / 0.5) & 0xFF
        # BMS_State=3 (Discharging) in bits[8:12], Error_Flags=0 in bits[12:16]
        b1 = (3 & 0x0F) | ((0 & 0x0F) << 4)
        counter = self._tick & 0xFF
        checksum = (soc_raw + b1 + counter) & 0xFF
        data = bytes([soc_raw, b1, counter, checksum, 0, 0, 0, 0])
        bus_manager.send(can.Message(arbitration_id=0x100, data=data, is_extended_id=False))

    def _send_pack_vals(self):
        # Pack voltage 380-420 V oscillating, scale 0.1
        voltage = 400.0 + 20.0 * math.sin(self._tick * 0.05)
        voltage_raw = int(voltage / 0.1) & 0xFFFF
        # Pack current -50 to +50 A (signed 16-bit), scale 0.1
        current = 30.0 * math.sin(self._tick * 0.08)
        current_raw = int(current / 0.1) & 0xFFFF
        # Avg cell voltage 3.65 V, scale 0.001
        avg_raw = int(3.65 / 0.001) & 0xFFFF
        # Voltage deviation 15 mV, scale 0.001
        dev_raw = int(0.015 / 0.001) & 0xFF
        data = bytes([
            voltage_raw & 0xFF, (voltage_raw >> 8) & 0xFF,
            current_raw & 0xFF, (current_raw >> 8) & 0xFF,
            avg_raw & 0xFF,     (avg_raw >> 8) & 0xFF,
            dev_raw, 0,
        ])
        bus_manager.send(can.Message(arbitration_id=0x101, data=data, is_extended_id=False))

    def _send_temps(self):
        # Temps gently oscillating around 25 °C, DBC offset -40 → raw = temp + 40
        base = 25.0 + 10.0 * math.sin(self._tick * 0.02)
        t_max = int(base + 5.0 + 40) & 0xFF
        t_min = int(base - 3.0 + 40) & 0xFF
        t_avg = int(base + 1.0 + 40) & 0xFF
        data = bytes([t_max, t_min, t_avg, 0, 0, 0, 0, 0])
        bus_manager.send(can.Message(arbitration_id=0x102, data=data, is_extended_id=False))


bms_simulator = BMSSimulator()
