"""
AutoTest Studio test script.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import can
from framework.decorators import on_start, on_stop, on_message, every
from framework.testcase import TestCase
from core.bus import bus_manager
from core.logger import logger

tc = TestCase("My_Test")


@on_start
def initialize():
    bus_manager.connect(interface="virtual", channel="vcan0")


@on_stop
def cleanup():
    bus_manager.disconnect()


@on_message(0x100)
def handle_status(msg: can.Message):
    soc = msg.data[0] * 0.5
    tc.expect_in_range(soc, 0, 100, "SOC")


@every(100)
def heartbeat():
    pass

