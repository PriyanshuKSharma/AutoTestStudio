# Frontend Documentation

## Overview

The frontend is a React + Vite dashboard in `frontend/src`. It provides a CANoe-style operator interface for live trace inspection, telemetry monitoring, fault injection, event review, diagnostics, and webhook configuration.

## Important Files

| File | Purpose |
| --- | --- |
| `frontend/src/App.jsx` | Main dashboard component and application state management. |
| `frontend/src/App.css` | Dashboard layout, panels, tables, controls, charts, and responsive styling. |
| `frontend/src/index.css` | Global theme variables, typography, reset, and scrollbar styles. |
| `frontend/src/main.jsx` | React application entry point. |
| `frontend/vite.config.js` | Vite dev-server configuration. |

## Dashboard Areas

| Area | Function |
| --- | --- |
| Header | Shows bus status, BMS state, and message rate. |
| Trace window | Displays decoded CAN frames with time, ID, name, DLC, raw payload, and signals. |
| Telemetry indicators | Shows SOC, pack voltage, pack current, and max cell temperature. |
| Gauges | Shows compact SOC and temperature indicators. |
| Trend charts | Shows voltage and current history. |
| Fault injection panel | Sends fault injection commands to the backend. |
| Event list | Shows recent backend event logs. |
| Diagnostics panel | Displays AI or heuristic analysis for selected events. |
| Webhook panel | Registers and removes automation webhook URLs. |

## Runtime Configuration

The frontend derives backend URLs from the current browser host by default:

```text
API: http://<browser-host>:8000
WS:  ws://<browser-host>:8000/ws
```

Override with environment variables:

```bash
set VITE_API_BASE=http://localhost:8000
set VITE_WS_URL=ws://localhost:8000/ws
```

## WebSocket Behavior

On load, the frontend connects to `/ws`, receives an initial snapshot, then processes:

| Type | Frontend Action |
| --- | --- |
| `init` | Seeds trace history, metrics, and charts. |
| `trace` | Appends a row to the trace table unless paused. |
| `metrics` | Updates indicators, gauges, and history charts. |
| `event` | Refreshes the event log list. |

If the WebSocket disconnects, the frontend reconnects automatically.

## Professional UI Standard

The dashboard uses compact technical labels such as `CAN`, `BMS`, `DTC`, `SOC`, `V`, `A`, and `C` instead of decorative emoji icons. This keeps the interface suitable for engineering demos and stakeholder reviews.

