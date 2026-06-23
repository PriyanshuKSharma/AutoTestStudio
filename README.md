# Virtual Web CANoe Simulator

Web-based CAN bus and BMS simulation platform for development, demos, signal analysis, and AI automation workflows.

The simulator generates virtual BMS CAN frames, decodes them with a DBC file, streams live trace data to a React dashboard, supports fault injection, stores events, and can forward fault events to n8n or an AI diagnostics workflow.

## Highlights

- Virtual BMS CAN traffic generation at 100 ms intervals.
- DBC-based CAN frame encoding and decoding with `cantools`.
- Live browser trace window with CAN ID, DLC, payload, and decoded signals.
- Real-time telemetry dashboard for SOC, voltage, current, temperature, BMS state, and message rate.
- Fault injection for over-voltage, under-voltage, and over-temperature scenarios.
- SQLite event logging with signal snapshots.
- REST API and WebSocket streaming interface.
- n8n webhook integration for automation workflows.
- Optional OpenAI-based diagnostics with local heuristic fallback.

## System Overview

```text
React Dashboard
    |
    | REST + WebSocket
    v
FastAPI Backend
    |
    | python-can virtual bus
    | cantools DBC encode/decode
    v
Virtual BMS CAN Simulator
    |
    | SQLite events
    | Webhook events
    v
n8n / AI diagnostics / ticketing tools
```

## Tech Stack

| Area | Technology |
| --- | --- |
| Frontend | React, Vite |
| Backend | Python, FastAPI |
| Realtime | WebSockets |
| CAN simulation | python-can virtual interface |
| DBC handling | cantools |
| Storage | SQLite |
| Automation | n8n webhooks |
| Deployment | Docker Compose |

## Quick Start

### Run With Docker Compose

```bash
docker compose up --build
```

Open the dashboard:

```text
http://localhost:3000
```

Backend API:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

### Run Locally

Start the backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Dashboard Capabilities

| Area | Description |
| --- | --- |
| Bus status | Shows WebSocket connection state, BMS mode, and message rate. |
| Trace window | Displays live decoded CAN frames. |
| Telemetry | Shows SOC, pack voltage, pack current, and max cell temperature. |
| Trend charts | Tracks voltage and current history. |
| Fault injection | Triggers OV, UV, OT, and clear-fault commands. |
| Event log | Lists recent simulation and fault events. |
| Diagnostics | Runs AI or local heuristic analysis for selected events. |
| Webhooks | Registers n8n or other automation endpoints. |

## CAN Messages

The included DBC file is located at:

```text
backend/bms.dbc
```

| CAN ID | Message | Purpose |
| --- | --- | --- |
| `0x100` | `BMS_Status` | SOC, BMS state, error flags, counter, checksum |
| `0x101` | `BMS_PackVals` | Pack voltage, pack current, average cell voltage, voltage deviation |
| `0x102` | `BMS_Temps` | Max, min, and average cell temperature |

Expected bus rate is approximately 30 messages per second because the simulator sends three CAN frames every 100 ms.

## Fault Injection

Faults can be triggered from the dashboard or through the REST API.

```bash
curl -X POST http://localhost:8000/api/faults/inject ^
  -H "Content-Type: application/json" ^
  -d "{\"fault_type\":\"over_voltage\"}"
```

Supported values:

```text
over_voltage
under_voltage
over_temperature
clear
```

## API Summary

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Backend and simulator health. |
| `GET` | `/api/metrics` | Current telemetry snapshot. |
| `GET` | `/api/dbc/messages` | DBC message metadata. |
| `POST` | `/api/faults/inject` | Inject or clear a fault. |
| `GET` | `/api/faults/active` | Active fault state. |
| `GET` | `/api/events` | Recent event logs. |
| `POST` | `/api/analyze/{event_id}` | AI or heuristic diagnostics. |
| `POST` | `/api/webhooks` | Register webhook. |
| `GET` | `/api/webhooks` | List webhooks. |
| `DELETE` | `/api/webhooks/{hook_id}` | Delete webhook. |

WebSocket stream:

```text
ws://localhost:8000/ws
```

## AI Diagnostics

The simulator works without an OpenAI key. When no key is configured, it uses a local heuristic diagnostics engine.

To enable OpenAI-backed diagnostics:

```bash
set OPENAI_API_KEY=your_api_key_here
```

For Docker Compose, add it to the backend service environment:

```yaml
environment:
  - OPENAI_API_KEY=your_api_key_here
```

## n8n Integration

Register an n8n webhook URL from the dashboard or with `/api/webhooks`. Each injected fault sends a structured payload containing the event type, severity, timestamp, message, and signal snapshot.

Recommended workflow:

```text
Webhook Trigger
  -> Severity filter
  -> AI root-cause summary
  -> Jira issue creation
  -> Team notification
  -> Event archive
```

When the backend runs in Docker and n8n runs on the host, use:

```text
http://host.docker.internal:5678/webhook/<id>
```

## Project Structure

```text
canoe_simulator/
  backend/              FastAPI backend, simulator, DBC, SQLite database
  frontend/             React dashboard
  docs/                 Detailed subsystem documentation
  docker-compose.yml    Container orchestration
  run_local.bat         Local Windows launcher
  README.md             Project overview
```

## Documentation

| Document | Description |
| --- | --- |
| [Architecture](docs/ARCHITECTURE.md) | System design, data lifecycle, and component boundaries. |
| [Backend](docs/BACKEND.md) | FastAPI, simulator lifecycle, events, diagnostics, and validation. |
| [Frontend](docs/FRONTEND.md) | Dashboard layout, WebSocket behavior, and UI standards. |
| [CAN and DBC](docs/CAN_DBC.md) | CAN frames, signals, state values, and error flags. |
| [API and WebSocket](docs/API_WEBSOCKET.md) | REST endpoints, WebSocket payloads, and commands. |
| [Automation and AI](docs/AUTOMATION_AI.md) | n8n flow, OpenAI behavior, payloads, and ticketing. |
| [Operations](docs/OPERATIONS.md) | Run commands, validation, troubleshooting, and Docker notes. |

## Validation

Validate DBC encode/decode behavior:

```bash
python backend\app\test_simulator.py
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Scope

This project is intended for simulation, workflow development, training, demos, and automation prototyping.

It is not a replacement for Vector CANoe, Vector hardware, CAPL execution, HIL validation, or safety-critical ECU verification.

