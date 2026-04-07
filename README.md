# DisasterGuard: Satellite Damage Assessment

End-to-end project for disaster damage classification from pre/post-event satellite imagery.

## Repository layout

- `frontend/` — Next.js dashboard for upload, analysis, hotspots, analytics, and reports.
- `backend/` — FastAPI inference API for model prediction and sample image endpoints.
- `ml/` — dataset preparation, training, evaluation, and prediction scripts.
- `data/` — local dataset storage (`raw/`, `prepared/`, `sample/`).
- `checkpoints/` — local model checkpoints and evaluation artifacts.

## Prerequisites

- Node.js 20+
- Python 3.11+

## Quick start

### 1. Backend + ML dependencies

```bash
pip install -r requirements.txt
```

### 2. Frontend dependencies

```bash
cd frontend
npm ci
```

### 3. Run backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Run frontend

```bash
cd frontend
npm run dev
```

Frontend uses Next.js rewrites to proxy API calls to `http://localhost:8000`.

By default, dashboard assessments/reports are **ephemeral** (not persisted).  
If you want persistence again, start frontend with:

```bash
NEXT_PUBLIC_PERSIST_ASSESSMENTS=true npm run dev
```

## Easy deployment alternatives (Mac-friendly)

If your Mac hangs with full dev mode (`--reload`, hot reload, extra workers), use these lightweight profiles:

### Lightweight backend (single worker, no reload)

```bash
bash scripts/run_backend_light.sh
```

Optional tuning:

```bash
BACKEND_PORT=8000 BACKEND_WORKERS=1 BACKEND_THREADS=1 bash scripts/run_backend_light.sh
```

### Lightweight frontend

Production mode is much lighter than `npm run dev` for day-to-day local usage:

```bash
bash scripts/run_frontend_light.sh
```

Use `FRONTEND_PROFILE=dev` only when you need live editing:

```bash
FRONTEND_PROFILE=dev bash scripts/run_frontend_light.sh
```

### One-command lightweight stack (start/stop)

```bash
bash scripts/start_lightweight_stack.sh
bash scripts/stop_lightweight_stack.sh
```

This starts backend + frontend in the background and writes logs to `runs/lightweight/logs/`.

### Offload heavy inference (recommended on constrained Macs)

Keep the frontend local, but point it to a stronger remote backend (VM/GPU box):

```bash
BACKEND_ORIGIN=https://your-remote-backend.example.com bash scripts/run_frontend_light.sh
```

or with the stack helper (frontend local + remote backend, no local model process):

```bash
START_LOCAL_BACKEND=0 BACKEND_ORIGIN=https://your-remote-backend.example.com bash scripts/start_lightweight_stack.sh
```

`frontend/next.config.ts` now reads `BACKEND_ORIGIN`, so `/api/*` requests are proxied to that remote backend while your UI stays local.


## Quality checks

### Frontend

```bash
cd frontend
npm run lint --silent
npm run build
```

### Python static compile checks

```bash
find backend/app ml -type f -name "*.py" -print0 | xargs -0 python3 -m py_compile
python3 -m py_compile backend/test.py test_ds.py
```

### Backend smoke test

```bash
python3 backend/test.py
```

## ML workflow

### Prepare dataset

```bash
python3 ml/prepare_dataset.py --input data/raw/train --output data/prepared --mode image
```

### Train model

```bash
python3 ml/train.py --data_dir data/prepared
```

### Evaluate model

```bash
python3 ml/evaluate.py --checkpoint checkpoints/best_model.pth --data_dir data/prepared
```

Training now writes reproducibility artifacts to `checkpoints/`:

- `training_config.json`
- `training_summary.json`
- `evaluation_metrics.json`
- `evaluation_report.txt`

## Artifact and cache hygiene

Use the cleanup helper to remove local generated caches safely:

```bash
bash scripts/cleanup_artifacts.sh
```

For broader generated artifact cleanup:

```bash
bash scripts/cleanup_artifacts.sh --all-generated
```

This does **not** remove `data/raw/`, `data/prepared/`, or model checkpoints by default.
