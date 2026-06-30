"""
Example BMS test using the AutoTest Studio framework.

CAPL equivalent:
    on message 0x100 { if(this.byte(0) < 20) write("Low SOC"); }
    on timer heartbeat { setTimer(heartbeat, 100); output(msg); }
"""

import os
import sys
import time

import can

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.bus import bus_manager
from core.logger import logger
from framework.decorators import (
    every,
    fire_message,
    fire_start,
    fire_stop,
    on_message,
    on_start,
    on_stop,
)
from framework.testcase import TestCase


# Create test case
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
    soc = msg.data[0] * 0.5
    tc.expect_in_range(soc, 0, 100, "SOC")

    if soc < 20:
        logger.fault("Low SOC detected", {"soc": soc})


@on_message(0x101)
def check_voltage(msg: can.Message):
    voltage = int.from_bytes(msg.data[0:2], "little") * 0.1
    tc.expect_in_range(voltage, 200, 450, "Pack Voltage")


@every(100)
def heartbeat():
    msg = can.Message(
        arbitration_id=0x7FF,
        data=[0xAA],
        is_extended_id=False,
    )

    try:
        bus_manager.send(msg)
    except Exception:
        pass


if __name__ == "__main__":
    fire_start()

    test_frames = [
        can.Message(
            arbitration_id=0x100,
            data=[0xA0, 0x03, 0x00, 0x01, 0xFF, 0, 0, 0],
            is_extended_id=False,
        ),
        can.Message(
            arbitration_id=0x101,
            data=[0xD0, 0x0F, 0x00, 0x00, 0xE8, 0x03, 0x05, 0x00],
            is_extended_id=False,
        ),
    ]

    for frame in test_frames:
        fire_message(frame.arbitration_id, frame)

    time.sleep(0.3)

    fire_stop()

    result = tc.summary()
    tc.save()

    print("\n" + "=" * 40)
    print(f"Test   : {result['name']}")
    print(f"Result : {result['result']}")
    print(f"Passed : {result['passed']}")
    print(f"Failed : {result['failed']}")

    for step in result["steps"]:
        print(f"[{step['status']}] {step['description']}")

    print("=" * 40)
