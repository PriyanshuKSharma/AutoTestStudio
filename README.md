# AutoTest Studio

> A desktop CAN bus test automation platform for BMS development — a Python alternative to Vector CANoe with CAPL-style scripting, live signal monitoring, fault injection, and SQLite-backed test reporting.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Layer Breakdown](#layer-breakdown)
- [GUI Panels](#gui-panels)
- [Data Flow](#data-flow)
- [CAN Bus Interfaces](#can-bus-interfaces)
- [DBC and Signal Decoding](#dbc-and-signal-decoding)
- [Test Framework](#test-framework)
- [Fault Injection](#fault-injection)
- [Database Schema](#database-schema)
- [Project State](#project-state)
- [Quick Start](#quick-start)
- [Writing Tests](#writing-tests)
- [Project Structure](#project-structure)

---

## Overview

AutoTest Studio connects to a virtual or physical CAN bus, decodes frames with a DBC file, runs automated test cases, and provides a full GUI for monitoring, sending, and fault injection. Everything persists in SQLite.

```mermaid
graph LR
    A["🖥️ AutoTest Studio\nDesktop GUI"] --> B["📡 CAN Bus\nvirtual / hardware"]
    B --> C["📦 DBC Decoder\ncantools"]
    C --> D["🗄️ SQLite\nResults · Events · Logs"]
    A --> E["🧪 Test Runner\nCAPL-style Python"]
    E --> D
    A --> F["⚡ Fault Injector\nOV · UV · OT"]
    F --> B
```

---

## Architecture

```mermaid
graph TB
    subgraph GUI["GUI Layer  (CustomTkinter)"]
        HOME["🏠 Home"]
        MON["📡 Monitor"]
        SND["📤 Sender"]
        SIG["📊 Signal Viewer"]
        DBC_EX["📖 DBC Explorer"]
        TB["🔧 Test Builder"]
        TR["▶️ Test Runner"]
        FI["⚡ Fault Injection"]
        RPT["📋 Reports"]
        SET["⚙️ Settings"]
    end

    subgraph CORE["Core Layer"]
        BM["BusManager\nbus.py"]
        DM["DBCManager\ndbc.py"]
        PROJ["Project\nproject.py"]
        LOG["EventLogger\nlogger.py"]
    end

    subgraph FW["Framework Layer"]
        TC["TestCase\ntestcase.py"]
        DEC["Decorators\ndecorators.py"]
        SCH["Scheduler\nscheduler.py"]
    end

    subgraph PLUG["Plugins"]
        VIRT["virtual.py\npython-can"]
        VEC["vector.py\nPCAN / XL / SocketCAN"]
    end

    subgraph DB["Persistence  (SQLite)"]
        T1["test_results"]
        T2["events"]
        T3["can_log"]
    end

    GUI --> CORE
    GUI --> FW
    CORE --> PLUG
    CORE --> DB
    FW --> DB
```

---

## Layer Breakdown

### Core Layer

```mermaid
classDiagram
    class BusManager {
        +interface: str
        +channel: str
        +bitrate: int
        +connect(interface, channel, bitrate) bool
        +disconnect()
        +send(msg: Message)
        +recv(timeout) Message
        +add_listener(callback)
        +connected: bool
    }

    class DBCManager {
        +path: str
        +load(path)
        +decode(can_id, data) dict
        +encode(name, signals) bytes
        +messages() list
        +get_message(can_id)
        +loaded: bool
    }

    class Project {
        +name: str
        +dbc_path: str
        +bus_interface: str
        +channel: str
        +bitrate: int
        +save(path)
        +load(path)
        +to_dict() dict
    }

    class EventLogger {
        +log(event_type, severity, message, signals)
        +fault(message, signals)
        +info(message, signals)
        +get_recent(limit) list
    }

    BusManager --> EventLogger : errors logged
    DBCManager --> BusManager : decoded frames
```

### Framework Layer

```mermaid
classDiagram
    class TestCase {
        +name: str
        +check(condition, description) bool
        +expect_equal(actual, expected, label) bool
        +expect_in_range(value, low, high, label) bool
        +passed: bool
        +summary() dict
        +save()
    }

    class Decorators {
        +on_start(fn)
        +on_stop(fn)
        +on_message(can_id)
        +every(interval_ms)
        +fire_start()
        +fire_stop()
        +fire_message(can_id, msg)
        +start_timers()
    }

    class Scheduler {
        +add(fn, interval_ms) entry
        +start_all()
        +stop_all()
    }

    TestCase --> Decorators : used inside handlers
    Decorators --> Scheduler : @every delegates to Scheduler
```

---

## GUI Panels

```mermaid
graph LR
    NAV["Sidebar\nNavigation"] --> HOME["🏠 Home\nStatus · Quick Start"]
    NAV --> MON["📡 CAN Monitor\nLive frame trace\nDBC decode · DB log"]
    NAV --> SND["📤 CAN Sender\nRaw frame · Cyclic\nDBC Signal Encoder"]
    NAV --> SIG["📊 Signal Viewer\nLive signal table\nUnit display"]
    NAV --> DBCE["📖 DBC Explorer\nMessages list\nSignal detail table"]
    NAV --> TB["🔧 Test Builder\nCode editor\nNew · Open · Save"]
    NAV --> TR["▶️ Test Runner\nSubprocess exec\nLive stdout · DB results"]
    NAV --> FI["⚡ Fault Injection\nOV · UV · OT · Clear\nRaw frame inject"]
    NAV --> RPT["📋 Reports\nTest Results tab\nEvent Log tab\nCAN Log tab · CSV export"]
    NAV --> SET["⚙️ Settings\nBus · Channel · Bitrate\nDBC path · Save project"]
```

| Panel | Key Actions |
| --- | --- |
| Home | Refresh bus/DBC status, quick-start guide |
| CAN Monitor | Start/Stop receive loop, decode with DBC, persist to `can_log` |
| CAN Sender | Build raw frames, cyclic transmission, encode signals via DBC |
| Signal Viewer | Start live decode, grid of signal name → live value → unit |
| DBC Explorer | Browse all messages and signal attributes (start, length, scale, unit) |
| Test Builder | Monospace editor pre-loaded with CAPL-style template, Open/Save |
| Test Runner | Browse and `subprocess` run any `.py` test, stream stdout, show history |
| Fault Injection | One-click OV/UV/OT DBC-encoded inject, raw frame inject, inject log |
| Reports | Three-tab view of `test_results`, `events`, `can_log`; CSV export |
| Settings | Connect/disconnect bus, browse DBC, save `project.json` |

---

## Data Flow

### Live Monitoring Flow

```mermaid
sequenceDiagram
    participant BUS as CAN Bus
    participant BM as BusManager
    participant MON as MonitorPanel
    participant DBC as DBCManager
    participant DB as SQLite

    MON->>BM: recv(timeout=0.5)
    BM->>BUS: read frame
    BUS-->>BM: can.Message
    BM-->>MON: can.Message
    MON->>DB: INSERT INTO can_log
    MON->>DBC: decode(can_id, data)
    DBC-->>MON: {signal: value, ...}
    MON->>MON: render row in scroll frame
```

### Test Execution Flow

```mermaid
sequenceDiagram
    participant USER as User
    participant TR as TestRunnerPanel
    participant PROC as subprocess (Python)
    participant TC as TestCase
    participant DB as SQLite

    USER->>TR: ▶ Run
    TR->>PROC: Popen([python, script.py])
    PROC->>TC: fire_start() → initialize()
    PROC->>TC: fire_message() → checks
    TC->>TC: expect_in_range / expect_equal
    PROC->>TC: fire_stop() → cleanup()
    TC->>DB: INSERT INTO test_results
    PROC-->>TR: stdout lines (streamed)
    TR->>TR: show ✓ Passed / ✗ Failed
    TR->>DB: reload recent results table
```

### Fault Injection Flow

```mermaid
sequenceDiagram
    participant USER as User
    participant FI as FaultInjectionPanel
    participant DBC as DBCManager
    participant BM as BusManager
    participant BUS as CAN Bus
    participant LOG as EventLogger
    participant DB as SQLite

    USER->>FI: click "Over Voltage"
    FI->>DBC: encode("BMS_Status", {SOC:80, BMS_State:4, Error_Flags:1})
    DBC-->>FI: bytes
    FI->>BM: send(can.Message(0x100, data))
    BM->>BUS: transmit frame
    FI->>LOG: fault("Fault injected: Over Voltage", payload)
    LOG->>DB: INSERT INTO events (severity=critical)
    FI->>FI: append to inject log box
```

### Settings / Bus Connect Flow

```mermaid
sequenceDiagram
    participant USER as User
    participant SET as SettingsPanel
    participant PROJ as Project
    participant BM as BusManager
    participant DBC as DBCManager

    USER->>SET: select interface, channel, bitrate
    USER->>SET: Browse DBC file
    SET->>DBC: load(path)
    DBC-->>SET: loaded ✓
    SET->>PROJ: project.dbc_path = path
    USER->>SET: Connect Bus
    SET->>BM: connect(interface, channel, bitrate)
    BM-->>SET: connected ✓
    SET->>PROJ: update bus_interface, channel, bitrate
    USER->>SET: Save Project
    SET->>PROJ: save() → project.json
```

---

## CAN Bus Interfaces

```mermaid
graph TD
    BM["BusManager\n(core/bus.py)"]
    BM --> VIRT["plugins/virtual.py\ninterface='virtual'\nchannel='vcan0'\nNo hardware needed"]
    BM --> PCAN["plugins/vector.py\ninterface='pcan'\nchannel='PCAN_USBBUS1'\nPeak PCAN adapter"]
    BM --> SOCK["plugins/vector.py\ninterface='socketcan'\nchannel='can0'\nLinux SocketCAN"]
    BM --> VEC["plugins/vector.py\ninterface='vector'\nVector XL hardware"]
```

| Interface | Plugin | When to use |
| --- | --- | --- |
| `virtual` | `virtual.py` | Development, CI, no hardware |
| `pcan` | `vector.py` | Peak PCAN USB adapter |
| `socketcan` | `vector.py` | Linux native CAN (can0, vcan0) |
| `vector` | `vector.py` | Vector VN/CANcaseXL hardware |

Supported bitrates: `125000`, `250000`, `500000`, `1000000` bps.

---

## DBC and Signal Decoding

The bundled DBC is at `AutoTestStudio/assets/bms.dbc`.

```mermaid
graph LR
    DBC_FILE["bms.dbc"] --> DM["DBCManager\ncantools"]
    DM --> D1["decode(0x100, bytes)\n→ {SOC, BMS_State, Error_Flags, ...}"]
    DM --> D2["decode(0x101, bytes)\n→ {Pack_Voltage, Pack_Current, ...}"]
    DM --> D3["decode(0x102, bytes)\n→ {Temp_Max, Temp_Min, Temp_Avg}"]
    DM --> E1["encode('BMS_Status', signals)\n→ bytes  (Sender / Fault Injection)"]
```

| CAN ID | Message | Signals |
| --- | --- | --- |
| `0x100` | `BMS_Status` | `SOC`, `BMS_State`, `Error_Flags`, `Counter`, `Checksum` |
| `0x101` | `BMS_PackVals` | `Pack_Voltage`, `Pack_Current`, `Cell_Voltage_Avg`, `Voltage_Dev` |
| `0x102` | `BMS_Temps` | `Temp_Max`, `Temp_Min`, `Temp_Avg` |

---

## Test Framework

### CAPL → Python mapping

```mermaid
graph LR
    A["CAPL: on start {}"] -->|Python| B["@on_start\ndef fn(): ..."]
    C["CAPL: on stop {}"] -->|Python| D["@on_stop\ndef fn(): ..."]
    E["CAPL: on message 0x100 {}"] -->|Python| F["@on_message(0x100)\ndef fn(msg): ..."]
    G["CAPL: setTimer(t, 100)"] -->|Python| H["@every(100)\ndef fn(): ..."]
```

### TestCase assertion methods

```mermaid
graph TD
    TC["TestCase('name')"]
    TC --> C["check(condition, description)\nRecords PASS / FAIL step"]
    TC --> EE["expect_equal(actual, expected, label)\nWraps check(actual == expected)"]
    TC --> EIR["expect_in_range(value, low, high, label)\nWraps check(low ≤ value ≤ high)"]
    TC --> SUM["summary()\nReturns name, passed, failed, steps, result"]
    TC --> SAVE["save()\nINSERT INTO test_results"]
```

### Full test lifecycle

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Running : fire_start()
    Running --> Listening : @on_start handlers execute
    Listening --> Checking : CAN frame received\nfire_message(can_id, msg)
    Checking --> Listening : step recorded (PASS/FAIL)
    Listening --> TimerTick : @every interval fires
    TimerTick --> Listening : timer handler executes
    Listening --> Stopping : fire_stop()
    Stopping --> Saved : tc.save() → SQLite
    Saved --> [*]
```

---

## Fault Injection

Preset faults are DBC-encoded and sent directly onto the bus:

```mermaid
graph TD
    FI["Fault Injection Panel"]
    FI --> OV["Over Voltage\nBMS_Status: BMS_State=4, Error_Flags=1\nCAN ID 0x100"]
    FI --> UV["Under Voltage\nBMS_Status: SOC=5, BMS_State=4, Error_Flags=2\nCAN ID 0x100"]
    FI --> OT["Over Temperature\nBMS_Temps: Temp_Max=75, Temp_Avg=58\nCAN ID 0x102"]
    FI --> CLR["Clear Faults\nBMS_Status: BMS_State=1, Error_Flags=0\nCAN ID 0x100"]
    FI --> RAW["Custom Raw Frame\nFree-form CAN ID + hex bytes"]
    OV --> LOG["EventLogger → SQLite events\nseverity = critical"]
    UV --> LOG
    OT --> LOG
    CLR --> LOG
```

---

## Database Schema

All data is stored in `autoteststudio.db` (SQLite, created automatically on first run).

```mermaid
erDiagram
    test_results {
        INTEGER id PK
        TEXT timestamp
        TEXT test_name
        TEXT status
        TEXT details
    }
    events {
        INTEGER id PK
        TEXT timestamp
        TEXT event_type
        TEXT severity
        TEXT message
        TEXT signals
    }
    can_log {
        INTEGER id PK
        TEXT timestamp
        TEXT can_id
        INTEGER dlc
        TEXT data
        TEXT channel
    }
```

| Table | Written by | Content |
| --- | --- | --- |
| `test_results` | `TestCase.save()` | Test name, PASS/FAIL, step array (JSON) |
| `events` | `EventLogger.log()` | Event type, severity, message, signal snapshot (JSON) |
| `can_log` | `MonitorPanel` | Every received frame (hex data, CAN ID, DLC, channel) |

---

## Project State

Session configuration is saved to and loaded from `project.json` automatically on startup.

```mermaid
graph LR
    START["app.py\nstartup"] --> LOAD["project.load()\nreads project.json"]
    LOAD --> RESTORE["Restores:\n• project name\n• DBC path\n• bus interface\n• channel\n• bitrate"]
    SET["Settings Panel\nSave Project"] --> SAVE["project.save()\nwrites project.json"]
```

`project.json` example:

```json
{
  "name": "BMS Validation",
  "dbc_path": "AutoTestStudio/assets/bms.dbc",
  "bus_interface": "virtual",
  "channel": "vcan0",
  "bitrate": 500000
}
```

---

## Quick Start

### Prerequisites

- Python 3.10 or later
- pip

### Windows (one-click)

```bat
run_local.bat
```

### Windows (manual)

```bat
cd AutoTestStudio
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Linux / macOS

```bash
cd AutoTestStudio
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### First-run workflow

```mermaid
graph TD
    A["Launch app.py"] --> B["Settings panel"]
    B --> C["Select Bus Interface\nvirtual / pcan / socketcan"]
    C --> D["Browse and load bms.dbc"]
    D --> E["Click Connect Bus"]
    E --> F{"Bus connected?"}
    F -- Yes --> G["Open CAN Monitor\nStart receiving frames"]
    F -- No --> B
    G --> H["Open Signal Viewer\nWatch live decoded values"]
    H --> I["Open Test Builder\nWrite or open a test script"]
    I --> J["Open Test Runner\nBrowse script → ▶ Run"]
    J --> K["View results in Reports"]
```

---

## Writing Tests

Tests live in `AutoTestStudio/tests/`. Every file is a standalone Python script that uses the framework decorators and `TestCase`.

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import can
from framework.decorators import on_start, on_stop, on_message, every, fire_start, fire_stop
from framework.testcase import TestCase
from core.bus import bus_manager
from core.logger import logger

tc = TestCase("BMS_Voltage_Check")

@on_start
def setup():
    bus_manager.connect(interface="virtual", channel="vcan0")

@on_message(0x101)
def check_voltage(msg: can.Message):
    voltage = int.from_bytes(msg.data[0:2], "little") * 0.1
    tc.expect_in_range(voltage, 200, 450, "Pack Voltage")

@on_message(0x100)
def check_soc(msg: can.Message):
    soc = msg.data[0] * 0.5
    tc.expect_in_range(soc, 0, 100, "SOC")
    if soc < 20:
        logger.fault("Low SOC", {"soc": soc})

@every(100)
def heartbeat():
    msg = can.Message(arbitration_id=0x7FF, data=[0xAA], is_extended_id=False)
    bus_manager.send(msg)

@on_stop
def teardown():
    tc.save()
    bus_manager.disconnect()

if __name__ == "__main__":
    fire_start()
    # inject test frames here
    fire_stop()
    result = tc.summary()
    print(f"{result['name']} → {result['result']}")
```

Run directly from the terminal:

```bash
python AutoTestStudio/tests/example_bms.py
```

Or use the Test Runner panel to browse and execute with live output streaming.

---

## Project Structure

```text
canoe_simulator_mqi/
├── AutoTestStudio/
│   ├── assets/
│   │   └── bms.dbc               BMS CAN message definitions
│   ├── core/
│   │   ├── bus.py                BusManager — connect, send, recv
│   │   ├── dbc.py                DBCManager — load, encode, decode
│   │   ├── logger.py             EventLogger — fault/info → SQLite events
│   │   └── project.py            Project — session state → project.json
│   ├── database/
│   │   └── sqlite.py             SQLite init, schema creation, connection
│   ├── framework/
│   │   ├── decorators.py         @on_start @on_stop @on_message @every
│   │   ├── scheduler.py          Periodic task scheduler (threading.Timer)
│   │   └── testcase.py           TestCase — check, expect_equal, expect_in_range, save
│   ├── gui/
│   │   ├── main_window.py        MainWindow — sidebar + panel stack
│   │   ├── home.py               Home panel
│   │   ├── monitor.py            CAN Monitor panel
│   │   ├── sender.py             CAN Sender panel
│   │   ├── signal_viewer.py      Signal Viewer panel
│   │   ├── dbc_explorer.py       DBC Explorer panel
│   │   ├── test_builder.py       Test Builder panel (code editor)
│   │   ├── test_runner.py        Test Runner panel (subprocess + results)
│   │   ├── fault_injection.py    Fault Injection panel
│   │   ├── reports.py            Reports panel (3 tabs + CSV export)
│   │   └── settings.py           Settings panel
│   ├── plugins/
│   │   ├── virtual.py            python-can virtual interface helper
│   │   └── vector.py             PCAN / Vector XL / SocketCAN helper
│   ├── tests/
│   │   └── example_bms.py        Example BMS test script
│   ├── app.py                    Entry point — load project, init DB, launch GUI
│   ├── config.py                 App-level defaults (bus, channel, DB path, version)
│   └── requirements.txt          Python dependencies
├── run_local.bat                 Windows one-click launcher
└── README.md                     This file
```

---

## Scope

AutoTest Studio is intended for simulation, test development, training, and automation prototyping.

It is not a replacement for Vector CANoe, Vector hardware, CAPL execution, HIL validation, or safety-critical ECU verification.
