# Architecture Documentation

## Purpose

The Virtual Web CANoe Simulator is a browser-accessible BMS CAN simulation environment. It is designed for development, demonstrations, AI workflow testing, n8n automation, and signal-analysis training.

The system models a BMS ECU that periodically publishes CAN frames. The backend encodes engineering values into raw CAN payloads, decodes those payloads through a DBC file, streams decoded frames to the browser, and logs fault events for downstream analysis.

## High-Level Flow

```text
React Dashboard
  -> REST commands and WebSocket subscription
FastAPI Backend
  -> CAN simulation, fault control, event storage
python-can Virtual Bus
  -> In-process virtual CAN channel
cantools DBC Decoder
  -> Raw frame to engineering value conversion
SQLite
  -> Fault event and webhook registration storage
n8n / AI / Jira
  -> Optional external automation
```

## Runtime Components

| Component | Responsibility |
| --- | --- |
| React dashboard | Shows trace data, telemetry, fault controls, event logs, diagnostics, and webhook configuration. |
| FastAPI application | Hosts REST endpoints, WebSocket endpoint, OpenAI/local diagnostics, and webhook management. |
| CAN simulator | Generates BMS state, pack values, and temperature frames every 100 ms. |
| DBC file | Defines signal bit positions, scaling, offsets, units, ranges, and value tables. |
| SQLite database | Stores fault events, signal snapshots, cached AI analysis, and webhook subscriptions. |
| n8n workflow | Receives fault webhook payloads and can create downstream automation actions. |

## Data Lifecycle

1. The simulator updates virtual BMS physics.
2. Engineering values are encoded into raw CAN frames.
3. Frames are sent on a `python-can` virtual bus.
4. The backend receives frames from the same virtual bus.
5. The DBC decoder converts raw bytes into physical signals.
6. Decoded trace rows are broadcast to WebSocket clients.
7. Metrics are broadcast for dashboard charts and gauges.
8. Fault injection creates an event log record.
9. Fault events are sent to registered webhooks.
10. AI analysis can be requested for any logged event.

## Boundaries

This project is intentionally scoped as a software simulator. It does not provide deterministic hardware timing, bus arbitration fidelity, CAPL compatibility, or safety validation.

