# Test Builder

## What Is It

Test Builder is the built-in code editor inside AutoTest Studio where engineers write Python test scripts for CAN bus validation. It is the direct replacement for writing CAPL scripts in Vector CANoe.

Instead of opening an external IDE or a text editor, you write your entire test logic here, save it as a `.py` file, and it is immediately ready to be run by the Test Runner.

---

## The Analogy

Think of Test Builder exactly like the CAPL Editor inside Vector CANoe.

In CANoe you open the CAPL editor, write event handlers like `on message`, `on start`, `on timer`, then compile and run them. The difference is that CAPL is a proprietary language that only runs inside CANoe.

Test Builder gives you the same structured event-driven approach but in standard Python. Any engineer who knows Python can read, write, and maintain the tests. No CANoe license is needed to author or review a test.

```
CANoe CAPL Editor          AutoTest Studio Test Builder
─────────────────          ────────────────────────────
Proprietary language   →   Standard Python
Compiles to CANoe      →   Plain .py file
Runs only in CANoe     →   Runs anywhere Python runs
Hard to version        →   Git-friendly text file
```

---

## What It Does

- Opens a full monospace code editor inside the application window
- Pre-loads a ready-to-use test template on every new file
- Lets you open any existing `.py` test file from disk
- Lets you save the current editor content to a file
- Tracks the current file path and shows it above the editor
- Does not execute code — execution is the job of the Test Runner

---

## The Framework Behind It

Test Builder uses the AutoTest Studio framework which lives in the `framework/` directory. The framework provides three things.

### 1. Decorators (`framework/decorators.py`)

These are the Python equivalents of CAPL event handlers.

| CAPL | Python |
|---|---|
| `on start {}` | `@on_start` |
| `on stop {}` | `@on_stop` |
| `on message 0x100 {}` | `@on_message(0x100)` |
| `on timer t1 { setTimer(t1, 100); }` | `@every(100)` |

Every function decorated with one of these will be called automatically at the right moment when the test runs.

### 2. TestCase (`framework/testcase.py`)

This is the assertion engine. Instead of manually writing `if` statements and printing results, you call methods on a `TestCase` object.

| Method | What it does |
|---|---|
| `tc.check(condition, "label")` | Records PASS if condition is True, FAIL otherwise |
| `tc.expect_equal(actual, expected, "label")` | Passes if actual == expected |
| `tc.expect_in_range(value, low, high, "label")` | Passes if low ≤ value ≤ high |
| `tc.summary()` | Returns a dict with name, passed count, failed count, all steps |
| `tc.save()` | Writes the result to the SQLite database |

### 3. Scheduler (`framework/scheduler.py`)

Powers the `@every(ms)` decorator. Runs timer-based functions in a background thread so they fire at regular intervals without blocking the test.

---

## The Template

Every new file starts with this template:

```python
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
```

This is a complete, runnable test. You only need to change the test name, the CAN IDs you care about, and the assertions inside each handler.

---

## How to Use It

### Writing a new test

1. Navigate to **Test Builder** in the sidebar
2. Click **New** — the template is loaded into the editor
3. Change `TestCase("My_Test")` to a meaningful name like `TestCase("BMS_OV_Validation")`
4. Replace or add `@on_message` handlers for the CAN IDs you want to validate
5. Write your assertions using `tc.expect_in_range` or `tc.expect_equal`
6. Click **Save As**, navigate to the `tests/` folder, and give the file a name like `test_bms_ov.py`

### Opening an existing test

1. Click **Open**
2. Browse to your `.py` test file
3. The file content loads into the editor and the file path is shown above the editor
4. Edit as needed and click **Save**

### Saving

- **Save** — overwrites the current file. If the file has never been saved it falls back to Save As.
- **Save As** — opens a file dialog to choose the destination and filename.

---

## Writing Assertions

### Check a signal is within a valid range

```python
@on_message(0x101)
def check_voltage(msg: can.Message):
    voltage = int.from_bytes(msg.data[0:2], "little") * 0.1
    tc.expect_in_range(voltage, 300.0, 450.0, "Pack Voltage")
```

### Check an exact value

```python
@on_message(0x100)
def check_state(msg: can.Message):
    bms_state = (msg.data[1] & 0x0F)
    tc.expect_equal(bms_state, 3, "BMS State should be Discharging")
```

### Check a raw condition

```python
@on_message(0x100)
def check_errors(msg: can.Message):
    error_flags = (msg.data[1] >> 4) & 0x0F
    tc.check(error_flags == 0, "No error flags should be set")
```

### Log a fault when something is wrong

```python
@on_message(0x100)
def check_soc(msg: can.Message):
    soc = msg.data[0] * 0.5
    tc.expect_in_range(soc, 20.0, 100.0, "SOC above minimum")
    if soc < 20.0:
        logger.fault("SOC below minimum threshold", {"soc": soc})
```

### Send a heartbeat every 100 ms

```python
@every(100)
def heartbeat():
    msg = can.Message(arbitration_id=0x7FF, data=[0xAA], is_extended_id=False)
    bus_manager.send(msg)
```

---

## Anatomy of a Complete Test File

```
┌─────────────────────────────────────────────┐
│  imports                                    │
│  sys.path setup                             │
├─────────────────────────────────────────────┤
│  tc = TestCase("Name")                      │  ← one TestCase per file
├─────────────────────────────────────────────┤
│  @on_start                                  │  ← connect bus, log start
│  def initialize(): ...                      │
├─────────────────────────────────────────────┤
│  @on_message(0xXXX)                         │  ← one handler per CAN ID
│  def check_something(msg): ...              │  ← decode + assert
├─────────────────────────────────────────────┤
│  @every(100)                                │  ← optional periodic task
│  def heartbeat(): ...                       │
├─────────────────────────────────────────────┤
│  @on_stop                                   │  ← save result, disconnect
│  def cleanup(): ...                         │
├─────────────────────────────────────────────┤
│  if __name__ == "__main__":                 │  ← entry point for runner
│      fire_start()                           │
│      # inject frames or wait               │
│      fire_stop()                            │
│      print(tc.summary())                   │
└─────────────────────────────────────────────┘
```

---

## Where Tests Are Stored

By convention all test files go in the `tests/` directory at the project root. You can store them anywhere on disk — the Test Builder does not enforce a location — but keeping them in `tests/` makes them easy to find from the Test Runner.

```
tests/
├── example_bms.py          ← shipped example
├── test_bms_voltage.py     ← your tests go here
├── test_bms_temperature.py
└── test_fault_injection.py
```

---

## What Test Builder Does NOT Do

- It does not run the test — use **Test Runner** for that
- It does not connect to the bus — that is done inside your `@on_start` handler
- It does not syntax-check or lint the code — it is a plain text editor
- It does not import or validate the framework — that happens at runtime

---

## Comparison with CAPL

```
CAPL (CANoe)                    Python (AutoTest Studio)
────────────────────────────    ────────────────────────────────────
on start { }                    @on_start
                                def initialize(): ...

on stop { }                     @on_stop
                                def cleanup(): ...

on message BMS_Status {         @on_message(0x100)
  float soc = this.SOC;         def check_status(msg):
  if (soc < 20)                     soc = msg.data[0] * 0.5
    write("Low SOC");               if soc < 20:
}                                       logger.fault("Low SOC")

msTimer t1;                     @every(100)
on timer t1 {                   def heartbeat():
  setTimer(t1, 100);                bus_manager.send(...)
  output(heartbeat_msg);
}

testcase BMS_Voltage {          tc = TestCase("BMS_Voltage")
  float v = getValue(..);       tc.expect_in_range(voltage,
  checkValue(v, 300, 450);          300, 450, "Pack Voltage")
}
```

The logic is identical. The syntax is standard Python.
