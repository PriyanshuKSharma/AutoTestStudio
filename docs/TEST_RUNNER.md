# Test Runner

## What Is It

Test Runner is the execution engine inside AutoTest Studio. It takes a Python test script written in Test Builder, runs it as a separate process, streams every line of its output live into the application window, and when the script finishes it reads the result from the database and displays it in a results table.

It is the direct replacement for clicking **Start** in Vector CANoe's test execution environment.

---

## The Analogy

In Vector CANoe, when you have a CAPL test module or a vTESTstudio test case, you press the green **Start** button on the measurement toolbar. CANoe internally compiles the CAPL, fires the `on start` event, starts listening for CAN messages, fires handlers as frames arrive, and when you press **Stop** it fires `on stop` and writes a test report to an `.xml` or `.html` file.

Test Runner does exactly the same thing but for Python scripts:

```
CANoe Test Execution               AutoTest Studio Test Runner
────────────────────               ───────────────────────────
Click Start in CANoe           →   Click ▶ Run in Test Runner
CANoe compiles CAPL            →   Python interprets the script
on start fires                 →   fire_start() is called
CAN frames arrive → handlers   →   fire_message() dispatches to handlers
on stop fires                  →   fire_stop() is called
Report written to .xml         →   Result saved to SQLite
View report in CANoe           →   View results in Reports panel
```

The test script itself is a completely standalone Python file. It can also be run directly from a terminal without opening the GUI at all — the runner just makes it convenient to do it from inside the application.

---

## What It Does

- Lets you browse to any `.py` test file on disk
- Runs the script as a subprocess using the same Python interpreter the app is running on
- Streams stdout and stderr line by line into a live output console in real time — you see every `print()` statement as it happens
- Detects the exit code — `0` means the test passed, anything else means it failed
- Reloads the last 20 results from the database after each run and shows them in a table at the bottom of the panel
- Lets you stop a running test mid-execution with the **Stop** button

---

## How Execution Works Internally

When you press **▶ Run**, the following sequence happens:

```
Test Runner Panel
      │
      │  subprocess.Popen([python, your_script.py])
      ▼
New Python Process
      │
      │  imports fire_start, fire_stop, TestCase, bus_manager
      │
      ├─ fire_start()
      │     └─ calls all @on_start decorated functions
      │           └─ e.g. bus_manager.connect(...)
      │
      ├─ your test body runs
      │     └─ fire_message() is called for each frame received
      │           └─ dispatches to matching @on_message handlers
      │                 └─ tc.expect_in_range(...) records PASS/FAIL
      │
      ├─ fire_stop()
      │     └─ cancels @every timers
      │     └─ calls all @on_stop decorated functions
      │           └─ tc.save() → INSERT INTO test_results
      │           └─ bus_manager.disconnect()
      │
      └─ process exits with code 0 (success) or 1 (failure)

Back in Test Runner Panel
      │
      ├─ stdout lines were streamed live into the output console
      ├─ exit code determines ✓ Passed or ✗ Failed status label
      └─ recent results table reloads from SQLite
```

The subprocess isolation is intentional. If a test crashes with an unhandled exception it cannot crash the GUI. The GUI stays running, shows the error output, and marks the test as failed.

---

## How to Use It

### Running a test

1. Navigate to **Test Runner** in the sidebar
2. Click **Browse** and select your `.py` test file
3. The file path appears next to the Browse button
4. Click **▶ Run**
5. Watch the output console — every `print()` from your script appears here in real time
6. When the script finishes the status label shows either **✓ Passed** or **✗ Failed (exit N)**
7. The recent results table at the bottom refreshes automatically

### Stopping a test mid-run

Click **Stop** — this sends a terminate signal to the subprocess. The test halts immediately. Any results that were already saved to the database before the stop remain in the database.

### Reading the output

The output console shows everything the script printed to stdout and stderr. A well-written test script prints something like this:

```
========================================
Test: BMS_Basic_Check  →  PASS
Steps: 2 passed, 0 failed
  [PASS] SOC: 80.0 in [0, 100]
  [PASS] Pack Voltage: 404.8 in [200, 450]
========================================
```

If the script raises an unhandled exception you will see the full Python traceback here, which tells you exactly what went wrong and on which line.

### Viewing history

The **Recent Results** table at the bottom always shows the last 20 test runs from the database. Each row shows:

| Column | Content |
|---|---|
| Status | PASS in green or FAIL in red |
| Test Name | The name passed to `TestCase("Name")` |
| Timestamp | When the test completed (UTC) |

For the full history with step-level detail, go to the **Reports** panel → Test Results tab.

---

## Running Without the GUI

Every test script is a standalone Python file. You can run it directly from a terminal at any time:

```bash
cd /path/to/project
python tests/test_bms_voltage.py
```

The output is printed to the terminal. The result is still saved to the SQLite database. This makes it possible to run tests in CI pipelines, from scripts, or from a scheduler without the GUI being open.

---

## What a Good Test Script Looks Like

```python
"""
BMS Over-Voltage Validation Test
Validates that the BMS correctly reports over-voltage state via CAN.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import can, time
from framework.decorators import on_start, on_stop, on_message, fire_start, fire_stop, fire_message
from framework.testcase import TestCase
from core.bus import bus_manager
from core.logger import logger

tc = TestCase("BMS_OV_Validation")


@on_start
def initialize():
    logger.info("OV validation test started")
    bus_manager.connect(interface="virtual", channel="vcan0")


@on_stop
def cleanup():
    tc.save()
    bus_manager.disconnect()
    result = tc.summary()
    print(f"\n{'='*40}")
    print(f"Test: {result['name']}  →  {result['result']}")
    print(f"Steps: {result['passed']} passed, {result['failed']} failed")
    for step in result['steps']:
        print(f"  [{step['status']}] {step['description']}")
    print('='*40)


@on_message(0x100)
def check_bms_status(msg: can.Message):
    soc       = msg.data[0] * 0.5
    bms_state = msg.data[1] & 0x0F
    error_flags = (msg.data[1] >> 4) & 0x0F

    tc.expect_in_range(soc, 0.0, 100.0, "SOC in valid range")
    tc.check(bms_state in range(6), "BMS State is a known value")
    tc.check(error_flags == 0, "No error flags set during normal operation")


@on_message(0x101)
def check_pack_vals(msg: can.Message):
    voltage = int.from_bytes(msg.data[0:2], "little") * 0.1
    tc.expect_in_range(voltage, 300.0, 450.0, "Pack Voltage in range")


if __name__ == "__main__":
    fire_start()

    # Inject normal operating frames
    fire_message(0x100, can.Message(
        arbitration_id=0x100,
        data=[0xC8, 0x03, 0x01, 0xCC, 0, 0, 0, 0],
        is_extended_id=False,
    ))
    fire_message(0x101, can.Message(
        arbitration_id=0x101,
        data=[0xD0, 0x0F, 0x00, 0x00, 0xE8, 0x03, 0x05, 0x00],
        is_extended_id=False,
    ))

    time.sleep(0.2)
    fire_stop()
```

---

## Status Indicators

| Label | Meaning |
|---|---|
| `Idle` | No test has been run yet |
| `Running…` | Script is currently executing |
| `✓ Passed` | Script exited with code 0 |
| `✗ Failed (exit 1)` | Script exited with a non-zero code |
| `✗ Failed (exit -1)` | The script could not be launched at all |

---

## Common Issues

### Nothing appears in the output console

The script ran but printed nothing. Add `print(tc.summary())` or a print statement at the end of your `@on_stop` function.

### ✗ Failed (exit 1) with a traceback

An unhandled Python exception occurred. Read the traceback in the output console — it tells you the file, line number, and error. Fix it in Test Builder and run again.

### ✗ Failed (exit 1) with no traceback

Your test logic failed — one or more `tc.check()` or `tc.expect_*()` calls returned FAIL. Look at the printed step summary to see which assertion failed and why.

### Script path says "None selected"

You have not browsed to a file yet. Click **Browse** first.

### Old results in the table

Click **▶ Run** again or navigate away and back — the table refreshes after every run automatically.

---

## How Results Are Stored

When `tc.save()` is called inside your `@on_stop` handler, a row is inserted into the `test_results` table in `autoteststudio.db`:

```sql
INSERT INTO test_results (timestamp, test_name, status, details)
VALUES ('2024-01-15T10:23:44', 'BMS_OV_Validation', 'PASS', '[...]');
```

The `details` column stores a JSON array of every step:

```json
[
  {"description": "SOC in valid range: 80.0 in [0.0, 100.0]", "status": "PASS"},
  {"description": "BMS State is a known value", "status": "PASS"},
  {"description": "Pack Voltage in range: 404.8 in [300.0, 450.0]", "status": "PASS"}
]
```

This is what the **Reports** panel reads and displays.

---

## Test Runner vs Test Builder — Side by Side

```
Test Builder                        Test Runner
────────────────────────────────    ────────────────────────────────
Write the test logic                Execute the test logic
Code editor with template           Subprocess executor
Save .py files to disk              Browse and select .py files
No bus connection needed            Bus connection happens in the script
No assertions evaluated             All assertions evaluated live
Output: a .py file                  Output: SQLite row + console log
```

They are designed to work together. Write in Builder, run in Runner.
