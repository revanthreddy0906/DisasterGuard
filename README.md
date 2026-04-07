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
