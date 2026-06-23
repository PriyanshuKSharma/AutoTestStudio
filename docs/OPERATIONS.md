# Operations Documentation

## Run With Docker Compose

```bash
docker compose up --build
```

Open:

```text
http://localhost:3000
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

## Run Locally

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Validation

DBC validation:

```bash
python backend\app\test_simulator.py
```

Frontend build:

```bash
cd frontend
npm run build
```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Dashboard does not connect | Confirm backend is running at `/api/health`. |
| Trace window is empty | Confirm WebSocket is connected and simulator is running. |
| Fault button fails | Check browser console and backend logs. |
| n8n does not receive events | Check webhook URL and Docker networking. |
| AI analysis uses fallback | Confirm `OPENAI_API_KEY` is set in the backend environment. |

## Docker Networking Note

When the backend runs in Docker and n8n runs on the host, do not use `localhost` for the n8n webhook from inside the container. Use:

```text
http://host.docker.internal:5678/webhook/<id>
```

