"""
Example BMS test using the AutoTest Studio framework.
Mirrors what would be written in CAPL — but in Python.

CAPL equivalent:
    on message 0x100 { if(this.byte(0) < 20) write("Low SOC"); }
    on timer heartbeat { setTimer(heartbeat, 100); output(msg); }
"""

import can
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from framework.decorators import on_start, on_stop, on_message, every, fire_start, fire_stop
from framework.testcase import TestCase
from core.bus import bus_manager
from core.logger import logger

tc = TestCase("BMS_Basic_Check")


@on_start
def initialize():
    logger.info("BMS test started")
    bus_manager.connect(interface="virtual", channel="vcan0")


@on_stop
def cleanup():
    logger.info("BMS test stopped")
    bus_manager.disconnect()


@on_message(0x100)
def check_soc(msg: can.Message):
    soc_raw = msg.data[0]
    soc = soc_raw * 0.5
    tc.expect_in_range(soc, 0, 100, "SOC")
    if soc < 20:
        logger.fault("Low SOC detected", {"soc": soc})


@on_message(0x101)
def check_voltage(msg: can.Message):
    voltage_raw = int.from_bytes(msg.data[0:2], "little")
    voltage = voltage_raw * 0.1
    tc.expect_in_range(voltage, 200, 450, "Pack Voltage")


@every(100)
def heartbeat():
    msg = can.Message(arbitration_id=0x7FF, data=[0xAA], is_extended_id=False)
    try:
        bus_manager.send(msg)
    except Exception:
        pass


if __name__ == "__main__":
    fire_start()

    # Simulate receiving a few messages manually for demo
    import time
    test_frames = [
        can.Message(arbitration_id=0x100, data=[0xA0, 0x03, 0x00, 0x01, 0xFF, 0,0,0], is_extended_id=False),
        can.Message(arbitration_id=0x101, data=[0xD0, 0x0F, 0x00, 0x00, 0xE8, 0x03, 0x05, 0x00], is_extended_id=False),
    ]
    from framework.decorators import fire_message
    for frame in test_frames:
        fire_message(frame.arbitration_id, frame)

    time.sleep(0.3)
    fire_stop()

    result = tc.summary()
    tc.save()
    print(f"\n{'='*40}")
    print(f"Test: {result['name']}  →  {result['result']}")
    print(f"Steps: {result['passed']} passed, {result['failed']} failed")
    for step in result['steps']:
        print(f"  [{step['status']}] {step['description']}")
    print('='*40)
