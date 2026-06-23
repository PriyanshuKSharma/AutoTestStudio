import os
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import requests

from .database import engine, Base, get_db
from .models import EventLog, WebhookSubscription
from .simulator import CANSimulator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FastAPIApp")

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Virtual CANoe Simulator API", version="1.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the global simulator
simulator = CANSimulator()

@app.on_event("startup")
async def startup_event():
    # Start the simulation threads
    simulator.start()
    logger.info("Application startup: CAN Simulator started.")

@app.on_event("shutdown")
async def shutdown_event():
    # Stop simulation
    simulator.stop()
    logger.info("Application shutdown: CAN Simulator stopped.")

# Websocket endpoint for real-time telemetry streaming
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    simulator.active_websockets.add(websocket)
    logger.info("Client connected to WebSocket trace")
    
    # Send initial snapshot of trace history and current metrics
    try:
        init_payload = {
            "type": "init",
            "data": {
                "trace_history": simulator.trace_history,
                "metrics": simulator.get_current_metrics()
            }
        }
        await websocket.send_text(json.dumps(init_payload))
        
        while True:
            # Keep socket alive. Receive messages if frontend wants to command simulator.
            data = await websocket.receive_text()
            # E.g. client could trigger fault via WebSocket
            cmd = json.loads(data)
            if cmd.get("action") == "inject_fault":
                simulator.set_fault(cmd.get("fault_type"))
    except WebSocketDisconnect:
        simulator.active_websockets.remove(websocket)
        logger.info("Client disconnected from WebSocket trace")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in simulator.active_websockets:
            simulator.active_websockets.remove(websocket)

# --- Pydantic Schemas ---
class FaultPayload(BaseModel):
    fault_type: str  # 'over_voltage', 'under_voltage', 'over_temperature', 'clear'

class WebhookCreate(BaseModel):
    name: str
    url: str

class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    created_at: str

    model_config = {"from_attributes": True}

class EventResponse(BaseModel):
    id: int
    timestamp: str
    event_type: str
    message: str
    severity: str
    signals_snapshot: Optional[str] = None
    ai_analysis: Optional[str] = None

# --- REST Endpoints ---

@app.post("/api/faults/inject")
def inject_fault(payload: FaultPayload):
    valid_types = ['over_voltage', 'under_voltage', 'over_temperature', 'clear']
    if payload.fault_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid fault_type. Choose from: {', '.join(valid_types)}"
        )
    
    simulator.set_fault(payload.fault_type)
    return {"status": "success", "active_faults": simulator.get_active_faults()}

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "simulator_running": simulator.running,
        "bus": "vcan0",
        "metrics": simulator.get_current_metrics()
    }

@app.get("/api/metrics")
def get_metrics():
    return simulator.get_current_metrics()

@app.get("/api/dbc/messages")
def get_dbc_messages():
    messages = []
    for message in simulator.db.messages:
        messages.append({
            "name": message.name,
            "frame_id": f"0x{message.frame_id:03X}",
            "length": message.length,
            "signals": [
                {
                    "name": signal.name,
                    "unit": signal.unit or "",
                    "minimum": signal.minimum,
                    "maximum": signal.maximum
                }
                for signal in message.signals
            ]
        })
    return messages

@app.get("/api/faults/active")
def active_faults():
    return {"active_faults": simulator.get_active_faults(), "state": simulator.get_state_string(simulator.state)}

@app.get("/api/events")
def get_events(db: Session = Depends(get_db)):
    events = db.query(EventLog).order_by(EventLog.timestamp.desc()).limit(50).all()
    
    result = []
    for e in events:
        result.append({
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "event_type": e.event_type,
            "message": e.message,
            "severity": e.severity,
            "signals_snapshot": e.signals_snapshot,
            "ai_analysis": e.ai_analysis
        })
    return result

@app.post("/api/webhooks")
def create_webhook(webhook: WebhookCreate, db: Session = Depends(get_db)):
    db_hook = db.query(WebhookSubscription).filter(WebhookSubscription.url == webhook.url).first()
    if db_hook:
        raise HTTPException(status_code=400, detail="Webhook URL already registered")
    
    new_hook = WebhookSubscription(name=webhook.name, url=webhook.url)
    db.add(new_hook)
    db.commit()
    db.refresh(new_hook)
    return {"id": new_hook.id, "name": new_hook.name, "url": new_hook.url}

@app.get("/api/webhooks")
def get_webhooks(db: Session = Depends(get_db)):
    hooks = db.query(WebhookSubscription).all()
    return [{"id": h.id, "name": h.name, "url": h.url, "created_at": h.created_at.isoformat()} for h in hooks]

@app.delete("/api/webhooks/{hook_id}")
def delete_webhook(hook_id: int, db: Session = Depends(get_db)):
    hook = db.query(WebhookSubscription).filter(WebhookSubscription.id == hook_id).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    db.delete(hook)
    db.commit()
    return {"status": "success", "message": f"Webhook subscription {hook_id} removed"}

@app.post("/api/analyze/{event_id}")
def analyze_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(EventLog).filter(EventLog.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if analysis is already cached
    if event.ai_analysis:
        return {"analysis": event.ai_analysis}
    
    # Try calling OpenAI API if key exists
    api_key = os.environ.get("OPENAI_API_KEY")
    signals_data = json.loads(event.signals_snapshot) if event.signals_snapshot else {}
    
    if api_key:
        try:
            logger.info("Calling OpenAI API for diagnostics...")
            prompt = (
                f"You are an expert Battery Management System (BMS) failure analysis engineer.\n"
                f"Analyze the following BMS fault log event:\n"
                f"Event Type: {event.event_type}\n"
                f"Log Message: {event.message}\n"
                f"BMS State during event: {signals_data.get('state')}\n"
                f"Pack voltage: {signals_data.get('voltage')} V\n"
                f"Pack current: {signals_data.get('current')} A\n"
                f"Max cell temperature: {signals_data.get('temp_max')} °C\n"
                f"Min cell temperature: {signals_data.get('temp_min')} °C\n"
                f"State of Charge (SOC): {signals_data.get('soc')} %\n\n"
                f"Provide a root cause analysis in 3 brief bullet points: "
                f"1. Identified Defect & Impact, 2. Highly Probable Engineering Cause, 3. Recommended Corrective Action."
            )
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": "You are a precise engineering assistant. Return markdown format."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 300
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                ai_text = response.json()['choices'][0]['message']['content'].strip()
                event.ai_analysis = ai_text
                db.commit()
                return {"analysis": ai_text}
            else:
                logger.warning(f"OpenAI returned non-200: {response.text}")
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")

    # Fallback to local heuristic model (Mock AI Engineer)
    logger.info("Generating diagnostics using local heuristic engine...")
    ai_text = generate_local_diagnostics(event.event_type, signals_data)
    event.ai_analysis = ai_text
    db.commit()
    return {"analysis": ai_text}

def generate_local_diagnostics(event_type: str, signals: dict) -> str:
    """Generate high-fidelity structured analysis responses if LLM is unavailable."""
    soc = signals.get('soc', 50.0)
    voltage = signals.get('voltage', 360.0)
    current = signals.get('current', 0.0)
    t_max = signals.get('temp_max', 35.0)

    if event_type == "OVER_VOLTAGE":
        return (
            f"### BMS Failure Analysis Report (Local Heuristic Engine)\n\n"
            f"* **Identified Defect:** Cell/Pack over-voltage condition detected. Pack voltage exceeded upper limit of 408.0V (measured **{voltage}V**).\n"
            f"* **Likely Cause:** Charger failed to terminate cycle or a cell capacity degradation imbalance. Cell voltages drifted above safety setpoints while current was still flowing (**{current}A**).\n"
            f"* **Remedial Action:** Check charger CAN communication links. Run a cell balancing procedure. Inspect for defective voltage sensor references on module board 1."
        )
    elif event_type == "UNDER_VOLTAGE":
        return (
            f"### BMS Failure Analysis Report (Local Heuristic Engine)\n\n"
            f"* **Identified Defect:** Deep cell discharge warning. Pack voltage dropped below emergency cutoff limit of 290.0V (measured **{voltage}V**).\n"
            f"* **Likely Cause:** Excessive parasitic drawing under low SOC (**{soc}%**), or cells capacity degradation. Severe load conditions (**{current}A**) caused sudden voltage sag below thresholds.\n"
            f"* **Remedial Action:** Disconnect load contactors immediately. Verify low-power sleep modes in BMS firmware. Perform diagnostic charging cycles at low current."
        )
    elif event_type == "OVER_TEMPERATURE":
        return (
            f"### BMS Failure Analysis Report (Local Heuristic Engine)\n\n"
            f"* **Identified Defect:** Thermal runaway warning. Maximum cell temperature reached **{t_max}°C**, exceeding warning limit (55.0°C) and critical limit (65.0°C).\n"
            f"* **Likely Cause:** Sustained high load current (**{current}A**) causing excessive $I^2R$ resistive heating in module cells, combined with potential cooling fan relay failure.\n"
            f"* **Remedial Action:** Verify cooling fan operations. Measure cell internal resistance (DCR) for hotspots. Reduce max charge/discharge limits under high ambient states."
        )
    else:
        return (
            f"### BMS Diagnostics Report (Local Heuristic Engine)\n\n"
            f"* **Identified State:** Simulation Event '{event_type}' logged. Current telemetry: {voltage}V, {current}A, {t_max}°C, SOC {soc}%.\n"
            f"* **Likely Cause:** Manual user simulation event or state transition.\n"
            f"* **Remedial Action:** Standard operations confirmed. Monitor live trace window to verify telemetry stabilization."
        )
