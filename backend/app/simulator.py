import asyncio
import os
import time
import random
import json
import logging
import cantools
import can
from typing import Set, Dict, List, Any
from sqlalchemy.orm import Session
import requests
import datetime
import contextlib

from .database import SessionLocal
from .models import EventLog, WebhookSubscription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CANSimulator")

class CANSimulator:
    def __init__(self):
        self.dbc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bms.dbc")
        self.db = cantools.database.load_file(self.dbc_path)
        
        # Virtual bus setup
        # python-can virtual bus interface
        self.bus = can.interface.Bus(
            interface='virtual',
            channel='vcan0',
            receive_own_messages=True
        )
        
        self.active_websockets: Set[Any] = set()
        self.trace_history: List[Dict[str, Any]] = []
        self.max_history_len = 100
        
        # Simulation parameters (BMS State Variables)
        self.soc = 80.0                # State of charge (%)
        self.state = 1                 # 0: Init, 1: Ready, 2: Charging, 3: Discharging, 4: Fault, 5: Shutdown
        self.error_flags = 0           # Error bitmask
        self.cell_volt = 3.9           # Average cell voltage (V)
        self.cell_volt_dev = 0.01      # Deviation (V)
        self.cell_temp = 28.0          # Average temperature (C)
        self.pack_current = -5.0       # Pack current (A)
        self.fault_state = "none"      # active fault injection: 'none', 'over_voltage', 'under_voltage', 'over_temperature'
        
        # Internals
        self.running = False
        self.send_task = None
        self.recv_task = None
        self.message_counter = 0
        self.start_time = time.time()
        self.msg_count_last_sec = 0
        self.msg_rate = 0
        self.rate_task = None
        self.loop = None

    def start(self):
        if not self.running:
            self.running = True
            self.loop = asyncio.get_running_loop()
            self.start_time = time.time()
            self.send_task = asyncio.create_task(self._send_loop())
            self.recv_task = asyncio.create_task(self._recv_loop())
            self.rate_task = asyncio.create_task(self._calculate_message_rate())
            logger.info("CAN Simulator started on virtual channel vcan0")

    def stop(self):
        self.running = False
        if self.send_task:
            self.send_task.cancel()
        if self.recv_task:
            self.recv_task.cancel()
        if self.rate_task:
            self.rate_task.cancel()
        with contextlib.suppress(Exception):
            self.bus.shutdown()
        logger.info("CAN Simulator stopped")

    def set_fault(self, fault_type: str):
        self.fault_state = fault_type
        db_session = SessionLocal()
        try:
            timestamp = datetime_now = datetime_from_timestamp(time.time())
            
            if fault_type == "over_voltage":
                self.error_flags |= 0x01
                self.state = 4  # Fault
                msg_text = "Critical Fault Injected: PACK OVER-VOLTAGE detected."
                severity = "ERROR"
            elif fault_type == "under_voltage":
                self.error_flags |= 0x02
                self.state = 4  # Fault
                msg_text = "Critical Fault Injected: PACK UNDER-VOLTAGE detected."
                severity = "ERROR"
            elif fault_type == "over_temperature":
                self.error_flags |= 0x04
                self.state = 4  # Fault
                msg_text = "Critical Fault Injected: PACK OVER-TEMPERATURE detected."
                severity = "ERROR"
            elif fault_type == "clear":
                self.fault_state = "none"
                self.error_flags = 0
                self.state = 1  # Back to Ready
                self.cell_volt = 3.8
                self.cell_temp = 30.0
                self.pack_current = -5.0
                msg_text = "BMS Fault Status Cleared. System Normal."
                severity = "INFO"
            else:
                msg_text = f"Custom simulation state: {fault_type}"
                severity = "INFO"

            # Create event log in SQLite
            event = EventLog(
                event_type=fault_type.upper(),
                message=msg_text,
                severity=severity,
                signals_snapshot=json.dumps(self.get_current_metrics())
            )
            db_session.add(event)
            db_session.commit()
            db_session.refresh(event)

            event_payload = {
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "message": event.message,
                "severity": event.severity,
                "signals": json.loads(event.signals_snapshot) if event.signals_snapshot else {}
            }
            
            # Trigger webhooks in the background
            self._schedule(self.trigger_webhooks(event_payload))
            
            # Notify trace subscribers
            self.broadcast_event_log(event_payload)
        except Exception as e:
            logger.error(f"Error handling fault injection: {e}")
        finally:
            db_session.close()

    def get_current_metrics(self) -> Dict[str, Any]:
        pack_voltage = self.cell_volt * 96  # 96 cells in series
        return {
            "soc": round(self.soc, 1),
            "voltage": round(pack_voltage, 1),
            "current": round(self.pack_current, 1),
            "temp_max": round(self.cell_temp + self.cell_volt_dev * 10, 1),
            "temp_min": round(self.cell_temp - self.cell_volt_dev * 10, 1),
            "temp_avg": round(self.cell_temp, 1),
            "state": self.get_state_string(self.state),
            "faults": self.get_active_faults(),
            "msg_rate": self.msg_rate,
            "error_flags": self.error_flags
        }

    def get_state_string(self, state_val: int) -> str:
        states = {0: "Init", 1: "Ready", 2: "Charging", 3: "Discharging", 4: "Fault", 5: "Shutdown"}
        return states.get(state_val, "Unknown")

    def get_active_faults(self) -> List[str]:
        faults = []
        if self.error_flags & 0x01: faults.append("OVER_VOLTAGE")
        if self.error_flags & 0x02: faults.append("UNDER_VOLTAGE")
        if self.error_flags & 0x04: faults.append("OVER_TEMPERATURE")
        if self.error_flags & 0x08: faults.append("UNDER_TEMPERATURE")
        return faults

    async def trigger_webhooks(self, event_payload: Dict[str, Any]):
        db_session = SessionLocal()
        try:
            webhooks = db_session.query(WebhookSubscription).all()
            if not webhooks:
                return

            payload = {
                "event_id": event_payload["id"],
                "timestamp": event_payload["timestamp"],
                "event_type": event_payload["event_type"],
                "message": event_payload["message"],
                "severity": event_payload["severity"],
                "signals": event_payload["signals"]
            }

            for hook in webhooks:
                logger.info(f"Firing webhook: {hook.name} -> {hook.url}")
                try:
                    # Run post request in run_in_executor to avoid blocking event loop
                    loop = asyncio.get_event_loop()
                    loop.run_in_executor(None, lambda: requests.post(hook.url, json=payload, timeout=3.0))
                except Exception as ex:
                    logger.error(f"Failed to post to webhook {hook.url}: {ex}")
        finally:
            db_session.close()

    def broadcast_event_log(self, event_payload: Dict[str, Any]):
        payload = {
            "type": "event",
            "data": event_payload
        }
        self.broadcast_json(payload)

    def broadcast_json(self, payload: Dict[str, Any]):
        if self.active_websockets:
            msg_str = json.dumps(payload)
            # Create a gather task to send to all connections concurrently
            futures = [ws.send_text(msg_str) for ws in self.active_websockets]
            self._schedule(self._send_gather(futures))

    def _schedule(self, coroutine):
        if not self.loop or self.loop.is_closed():
            logger.warning("Simulator event loop is not available for async task scheduling.")
            return
        try:
            running_loop = asyncio.get_running_loop()
            if running_loop is self.loop:
                asyncio.create_task(coroutine)
            else:
                asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        except RuntimeError:
            asyncio.run_coroutine_threadsafe(coroutine, self.loop)

    async def _send_gather(self, futures):
        try:
            await asyncio.gather(*futures, return_exceptions=True)
        except Exception:
            pass

    async def _calculate_message_rate(self):
        while self.running:
            await asyncio.sleep(1.0)
            self.msg_rate = self.msg_count_last_sec
            self.msg_count_last_sec = 0

    async def _send_loop(self):
        """Generates raw CAN messages and sends them on the virtual CAN bus."""
        while self.running:
            try:
                # 1. Update Simulation Physics
                self._update_physics()

                # 2. Increment rolling counter
                self.message_counter = (self.message_counter + 1) & 0xFF

                # 3. Create & Encode CAN Message 1: BMS_Status (0x100)
                status_msg = self.db.get_message_by_name('BMS_Status')
                status_data = status_msg.encode({
                    'BMS_SOC': self.soc,
                    'BMS_State': self.state,
                    'BMS_ErrorFlags': self.error_flags,
                    'BMS_Counter': self.message_counter,
                    'BMS_Checksum': 0  # Simplified checksum
                })
                can_msg_status = can.Message(
                    arbitration_id=status_msg.frame_id, 
                    data=status_data, 
                    is_extended_id=False
                )
                self.bus.send(can_msg_status)
                self.msg_count_last_sec += 1

                # 4. Create & Encode CAN Message 2: BMS_PackVals (0x101)
                pack_voltage = self.cell_volt * 96
                pack_vals_msg = self.db.get_message_by_name('BMS_PackVals')
                pack_data = pack_vals_msg.encode({
                    'BMS_PackVoltage': pack_voltage,
                    'BMS_PackCurrent': self.pack_current,
                    'BMS_AvgCellVolt': self.cell_volt,
                    'BMS_CellVoltDev': self.cell_volt_dev
                })
                can_msg_pack = can.Message(
                    arbitration_id=pack_vals_msg.frame_id, 
                    data=pack_data, 
                    is_extended_id=False
                )
                self.bus.send(can_msg_pack)
                self.msg_count_last_sec += 1

                # 5. Create & Encode CAN Message 3: BMS_Temps (0x102)
                temps_msg = self.db.get_message_by_name('BMS_Temps')
                max_temp = self.cell_temp + self.cell_volt_dev * 10
                min_temp = self.cell_temp - self.cell_volt_dev * 10
                temp_data = temps_msg.encode({
                    'BMS_MaxCellTemp': max_temp,
                    'BMS_MinCellTemp': min_temp,
                    'BMS_AvgCellTemp': self.cell_temp,
                    'BMS_TempSensorCount': 4
                })
                can_msg_temp = can.Message(
                    arbitration_id=temps_msg.frame_id, 
                    data=temp_data, 
                    is_extended_id=False
                )
                self.bus.send(can_msg_temp)
                self.msg_count_last_sec += 1

                # Send periodically every 100 ms
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in CAN simulator send loop: {e}")
                await asyncio.sleep(1.0)

    async def _recv_loop(self):
        """Reads raw CAN messages from the bus, decodes them, and streams via websocket."""
        while self.running:
            try:
                # Wait for a CAN message (non-blocking in executor or timeout)
                loop = asyncio.get_event_loop()
                msg = await loop.run_in_executor(None, lambda: self.bus.recv(timeout=0.5))
                if msg is None:
                    continue

                # Convert to log entry
                try:
                    db_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
                    msg_name = db_msg.name
                    decoded = db_msg.decode(msg.data, decode_choices=False)
                    
                    # Custom post-processing of decoded values for raw printouts
                    clean_decoded = {}
                    for k, v in decoded.items():
                        if k == 'BMS_State' and isinstance(v, int):
                            clean_decoded[k] = self.get_state_string(v)
                        elif isinstance(v, (int, float)):
                            clean_decoded[k] = round(v, 3)
                        else:
                            clean_decoded[k] = v
                except KeyError:
                    msg_name = "Unknown"
                    clean_decoded = {}

                # Format frame trace details
                payload_hex = msg.data.hex().upper()
                time_offset = round(time.time() - self.start_time, 4)
                
                trace_entry = {
                    "time": time_offset,
                    "id": f"0x{msg.arbitration_id:03X}",
                    "name": msg_name,
                    "dlc": msg.dlc,
                    "payload": payload_hex,
                    "signals": clean_decoded
                }

                # Maintain history list
                self.trace_history.append(trace_entry)
                if len(self.trace_history) > self.max_history_len:
                    self.trace_history.pop(0)

                # Broadcast to Websockets
                # 1. Trace Window log
                self.broadcast_json({
                    "type": "trace",
                    "data": trace_entry
                })

                # 2. Metrics update (broadcasted less frequently or on every message)
                # Let's broadcast metrics on every BMS_Status update
                if msg_name == "BMS_Status":
                    self.broadcast_json({
                        "type": "metrics",
                        "data": self.get_current_metrics()
                    })

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in CAN simulator recv loop: {e}")
                await asyncio.sleep(0.5)

    def _update_physics(self):
        """Simulates physical dynamics of a battery pack."""
        import datetime
        
        # Check active fault injections
        if self.fault_state == "over_voltage":
            # Simulate high voltage condition
            self.cell_volt = min(4.35, self.cell_volt + 0.03)
            self.soc = min(100.0, self.soc + 0.5)
            self.pack_current = 25.0
            self.error_flags |= 0x01
            self.state = 4
        elif self.fault_state == "under_voltage":
            # Simulate depletion
            self.cell_volt = max(2.6, self.cell_volt - 0.03)
            self.soc = max(0.0, self.soc - 0.5)
            self.pack_current = -60.0
            self.error_flags |= 0x02
            self.state = 4
        elif self.fault_state == "over_temperature":
            # Simulate runaway/overheating
            self.cell_temp = min(80.0, self.cell_temp + 1.2)
            self.pack_current = -85.0
            self.error_flags |= 0x04
            self.state = 4
        else:
            # NORMAL OPERATION
            # Dynamic simulation based on active states (Ready, Charging, Discharging)
            if self.state == 4:
                # Recovered from fault
                self.state = 1
                
            # State Transitions
            if self.state == 1:  # Ready - Idle draw
                self.pack_current = -0.5
                self.soc = max(0.0, self.soc - 0.0001)
                
                # Slow temperature recovery to ambient (25.0C)
                self.cell_temp += (25.0 - self.cell_temp) * 0.05
                
                # Cell voltage relaxes toward open circuit voltage (OCV)
                target_cell_volt = 3.0 + (self.soc / 100.0) * 1.1  # 3.0 to 4.1 V
                self.cell_volt += (target_cell_volt - self.cell_volt) * 0.1
                
                # Transition to discharging randomly for demo purposes, or can be triggered
                if random.random() < 0.01:
                    self.state = 3  # Start Discharging
                elif random.random() < 0.005 and self.soc < 50:
                    self.state = 2  # Start Charging
                    
            elif self.state == 2:  # Charging
                # Max charging current, decreases as SOC approaches full
                self.pack_current = max(1.0, 45.0 * (1.0 - (self.soc / 100.0)))
                self.soc = min(100.0, self.soc + (self.pack_current * 0.1) / 360.0)
                
                # Voltage rises with charging current (internal resistance)
                ocv = 3.0 + (self.soc / 100.0) * 1.1
                self.cell_volt = ocv + (self.pack_current * 0.0015)
                
                # Temperature rises slightly with current
                self.cell_temp += (self.pack_current * 0.005) - (self.cell_temp - 25.0) * 0.02
                
                if self.soc >= 100.0:
                    self.state = 1  # Charging complete
                    self.pack_current = 0
                    
            elif self.state == 3:  # Discharging (Dynamic Loads)
                # Random load jumps
                self.pack_current = -12.0 + random.uniform(-35.0, 5.0)
                # Ensure load is negative
                self.pack_current = min(-0.1, self.pack_current)
                
                self.soc = max(0.0, self.soc + (self.pack_current * 0.1) / 360.0)
                
                # Voltage drops with discharging current (internal resistance)
                ocv = 3.0 + (self.soc / 100.0) * 1.1
                self.cell_volt = ocv + (self.pack_current * 0.0015)
                
                # Temperature rises due to discharging current
                self.cell_temp += (abs(self.pack_current) * 0.008) - (self.cell_temp - 25.0) * 0.02
                
                if self.soc <= 5.0:
                    self.state = 5  # Shutdown due to empty battery
                    
            elif self.state == 5:  # Shutdown
                self.pack_current = 0.0
                self.cell_volt += (3.0 - self.cell_volt) * 0.2
                self.cell_temp += (25.0 - self.cell_temp) * 0.05
                if self.soc > 20.0:
                    self.state = 1  # Revive if charged

            # Small cell voltage variance fluctuation
            self.cell_volt_dev = 0.005 + 0.002 * random.random()

def datetime_from_timestamp(ts: float) -> datetime.datetime:
    return datetime.datetime.utcfromtimestamp(ts)
