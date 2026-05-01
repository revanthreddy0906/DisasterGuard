<![CDATA[<div align="center">

# 🛡️ DisasterGuard

**AI-Powered Satellite Imagery Damage Assessment Platform**

[![CI](https://github.com/revanthreddy0906/DisasterGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/revanthreddy0906/DisasterGuard/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?logo=pytorch&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

*Upload pre- and post-disaster satellite imagery, and let a Siamese neural network pinpoint structural damage at the patch level — all through a sleek, interactive dashboard.*

---

</div>

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [ML Pipeline](#ml-pipeline)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Quality Assurance](#quality-assurance)
- [Contributing](#contributing)

---

## Overview

**DisasterGuard** is a full-stack platform for rapid post-disaster building damage assessment using satellite imagery. It combines a custom **Siamese neural network** with a production-grade web dashboard, enabling disaster response teams to:

1. **Upload** pairs of pre- and post-disaster satellite images.
2. **Classify** structural damage into three severity levels — *No Damage*, *Severe Damage*, and *Destroyed*.
3. **Visualize** damage hotspots overlaid on the original imagery.
4. **Generate** analytical reports with per-assessment breakdowns, confidence scores, and damage distribution charts.

The ML model is trained on the [xBD dataset](https://xview2.org/) — the largest publicly available dataset for building damage assessment from overhead imagery.

---

## Key Features

| Feature | Description |
|---|---|
| **Siamese Damage Network** | Shared-encoder architecture (EfficientNet-B0) with feature fusion and Squeeze-and-Excitation attention |
| **Patch-Level Hotspot Detection** | Sliding-window analyzer breaks images into 224×224 patches with 50% overlap for granular localization |
| **Interactive Dashboard** | Dark-themed Next.js dashboard with real-time charts, assessment history, and damage distribution analytics |
| **Damage Heatmap Overlay** | Visual overlay showing per-patch predictions directly on satellite imagery |
| **Resilient Inference API** | FastAPI backend with concurrency guards, request timeouts, queue backpressure, and structured observability |
| **Lightweight Deployment** | One-command stack for local development on resource-constrained machines (Mac-friendly) |
| **CI/CD Pipeline** | GitHub Actions workflow for frontend lint/build and Python static analysis on every push |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 16)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ │
│  │Dashboard │ │ Upload   │ │ Analysis │ │Hotspots│ │ Reports │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ └─────────┘ │
│                        API Proxy (rewrites)                      │
└──────────────────────────┬───────────────────────────────────────┘
                           │ /api/v1/*
┌──────────────────────────▼───────────────────────────────────────┐
│                     Backend (FastAPI + Uvicorn)                   │
│  ┌─────────────┐  ┌────────────────┐  ┌────────────────────────┐│
│  │ Endpoints   │  │InferenceGuard  │  │  Observability         ││
│  │ /predict    │  │ concurrency    │  │  request metrics       ││
│  │ /sample     │  │ timeout        │  │  structured logging    ││
│  │ /health     │  │ backpressure   │  │  request tracing       ││
│  └──────┬──────┘  └────────────────┘  └────────────────────────┘│
│         │                                                        │
│  ┌──────▼──────────────────────────────────────────────────────┐ │
│  │              ML Inference Engine                             │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │ │
│  │  │ModelLoader   │  │PatchAnalyzer │  │ SiameseDamageNet  │  │ │
│  │  │(lazy load)   │  │(sliding win) │  │ (EfficientNet-B0) │  │ │
│  │  └─────────────┘  └──────────────┘  └───────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### ML Model Architecture

```
Pre-disaster image  ──►  ┌─────────────────────┐  ──► Pre-features (1280-d)
                         │  Shared EfficientNet  │                           ┐
Post-disaster image ──►  │  Encoder (B0)         │  ──► Post-features (1280-d)
                         └─────────────────────┘                           │
                                                                           ▼
                                                              ┌──────────────────┐
                                                              │  Feature Fusion   │
                                                              │  concat + |diff|  │
                                                              │  = 3840 features  │
                                                              └────────┬─────────┘
                                                                       ▼
                                                              ┌──────────────────┐
                                                              │   SE Attention    │
                                                              │  (channel-wise)  │
                                                              └────────┬─────────┘
                                                                       ▼
                                                              ┌──────────────────┐
                                                              │  Classifier MLP   │
                                                              │  3840→512→128→3   │
                                                              └────────┬─────────┘
                                                                       ▼
                                                              [no-damage | severe | destroyed]
```

**Key Design Decisions:**
- **Siamese weight sharing** ensures both temporal images are encoded identically, making change detection robust.
- **Feature Fusion** combines concatenation (`[pre | post]`) with absolute difference (`|pre − post|`) to capture both context and change.
- **Squeeze-and-Excitation** attention learns per-feature importance, suppressing noise in the 3840-d fused representation.
- **Focal Loss** with per-class alpha weights handles severe class imbalance (60%+ no-damage in xBD).
- **Two-stage training**: backbone frozen for 3 warmup epochs, then unfrozen with 10× lower LR for fine-tuning.

---

## Tech Stack

### Machine Learning
| Component | Technology |
|---|---|
| Framework | PyTorch 2.0+ |
| Backbone | EfficientNet-B0 (via `timm`) |
| Augmentation | Albumentations (synchronized pre/post transforms) |
| Loss Function | Focal Loss with label smoothing (γ=1.0) |
| Metrics | scikit-learn (F1, accuracy, confusion matrix) |
| Visualization | Matplotlib, Seaborn, TensorBoard |

### Backend
| Component | Technology |
|---|---|
| API Framework | FastAPI |
| Server | Uvicorn |
| Inference Guard | Custom concurrency limiter + timeout + backpressure |
| Observability | Structured JSON logging, request metrics, request tracing |
| Image Processing | Pillow |

### Frontend
| Component | Technology |
|---|---|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS 4 |
| UI Components | Radix UI + shadcn/ui |
| Charts | Recharts |
| Maps | MapLibre GL / Mapbox GL |
| Animations | Framer Motion |
| File Upload | react-dropzone |

### DevOps
| Component | Technology |
|---|---|
| CI/CD | GitHub Actions |
| Scripts | Bash (start/stop, cleanup, lightweight profiles) |
| Linting | ESLint (frontend), py_compile (backend) |

---

## Project Structure

```
DisasterGuard/
├── ml/                          # Machine Learning module
│   ├── config.py                #   Hyperparameters, paths, device selection
│   ├── model.py                 #   SiameseDamageNet, FeatureFusion, SEBlock
│   ├── dataset.py               #   XBDDataset, synchronized augmentation
│   ├── losses.py                #   Focal Loss implementation
│   ├── train.py                 #   Training loop with LR scheduling
│   ├── evaluate.py              #   Test-set evaluation and reporting
│   ├── predict.py               #   Single-image prediction utility
│   ├── prepare_dataset.py       #   Raw xBD → prepared folder structure
│   └── model_ops.py             #   Model loading and ONNX export helpers
│
├── backend/                     # FastAPI inference server
│   ├── app/
│   │   ├── main.py              #   App factory, middleware, health/metrics
│   │   ├── api/
│   │   │   ├── endpoints.py     #   /predict, /sample-images routes
│   │   │   └── validation.py    #   Upload validation helpers
│   │   ├── core/
│   │   │   ├── config.py        #   Server settings (ports, timeouts, paths)
│   │   │   ├── inference_guard.py  # Concurrency/timeout/backpressure
│   │   │   └── observability.py #   Structured logging and metrics
│   │   ├── schemas/             #   Pydantic response models
│   │   └── services/
│   │       ├── model_loader.py  #   Lazy model loading with caching
│   │       └── patch_analyzer.py#   Sliding-window damage hotspot detection
│   └── tests/                   #   Backend unit tests
│
├── frontend/                    # Next.js 16 dashboard
│   └── src/
│       ├── app/
│       │   ├── page.tsx         #   Dashboard with stats and charts
│       │   ├── upload/          #   Image upload with drag-and-drop
│       │   ├── analysis/        #   Per-assessment results viewer
│       │   ├── hotspots/        #   Damage heatmap overlay
│       │   ├── analytics/       #   Aggregate analytics and trends
│       │   └── reports/         #   Assessment report generation
│       ├── components/          #   Reusable UI components (layout, map, ui)
│       ├── context/             #   AssessmentContext (state management)
│       └── lib/                 #   Utilities
│
├── scripts/                     # Operational scripts
│   ├── start_lightweight_stack.sh   # One-command start (backend + frontend)
│   ├── stop_lightweight_stack.sh    # One-command stop
│   ├── run_backend_light.sh         # Lightweight backend (single worker)
│   ├── run_frontend_light.sh        # Lightweight frontend (production mode)
│   └── cleanup_artifacts.sh         # Remove generated caches
│
├── data/                        # Local dataset storage
│   ├── raw/                     #   Original xBD images
│   ├── prepared/                #   Train/val/test splits by class
│   └── sample/                  #   Sample images for demo
│
├── checkpoints/                 # Model checkpoints and evaluation artifacts
├── .github/workflows/ci.yml    # CI pipeline
├── requirements.txt             # Python dependencies
└── pyrightconfig.json           # Python type-checking config
```

---

## Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 20+ |
| npm | 10+ |

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/revanthreddy0906/DisasterGuard.git
cd DisasterGuard
```

**2. Install Python dependencies** (ML + Backend)

```bash
pip install -r requirements.txt
```

**3. Install Frontend dependencies**

```bash
cd frontend
npm ci
cd ..
```

### Running the Application

#### Option A: One-Command Stack (Recommended)

```bash
bash scripts/start_lightweight_stack.sh
```

This starts both backend (`http://localhost:8000`) and frontend (`http://localhost:3000`) in the background, with logs written to `runs/lightweight/logs/`.

Stop everything with:
```bash
bash scripts/stop_lightweight_stack.sh
```

#### Option B: Manual Start

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend** (in a separate terminal):
```bash
cd frontend
npm run dev
```

The frontend proxies `/api/*` requests to the backend via Next.js rewrites.

### Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_PERSIST_ASSESSMENTS` | `false` | Persist assessments across sessions |
| `NEXT_PUBLIC_MAX_UPLOAD_FILES` | `40` | Max files per upload batch |
| `NEXT_PUBLIC_MAX_FILE_SIZE_MB` | `25` | Max single file size |
| `NEXT_PUBLIC_MAX_TOTAL_UPLOAD_MB` | `300` | Max total upload size |
| `NEXT_PUBLIC_MAX_ACTIVE_ANALYSES` | `2` | Max concurrent analysis jobs |
| `BACKEND_ORIGIN` | `http://127.0.0.1:8000` | Backend URL for API proxy |
| `BACKEND_PORT` | `8000` | Backend server port |
| `BACKEND_WORKERS` | `1` | Uvicorn worker count |

---

## ML Pipeline

### 1. Dataset Preparation

Convert raw xBD imagery into a structured train/val/test split:

```bash
python3 ml/prepare_dataset.py --input data/raw/train --output data/prepared --mode image
```

This creates the folder structure:
```
data/prepared/
├── train/
│   ├── no-damage/       (pre_*.png, post_*.png)
│   ├── severe-damage/   (pre_*.png, post_*.png)
│   └── destroyed/       (pre_*.png, post_*.png)
├── val/
└── test/
```

**Class Merging:** Original xBD has 4 damage levels. We merge *minor-damage* and *major-damage* into **severe-damage** for cleaner, more balanced 3-class classification.

### 2. Training

```bash
python3 ml/train.py --data_dir data/prepared --epochs 50 --batch_size 32 --lr 1e-4
```

**Training Strategy:**
- **Epochs 1–3** (Warmup): EfficientNet backbone is frozen; only the fusion + classifier layers are trained.
- **Epochs 4–50** (Fine-tuning): Backbone unfrozen with 10× lower learning rate. Cosine annealing with warm restarts manages the schedule.
- **Focal Loss** (γ=1.0, label smoothing=0.15) addresses class imbalance.
- **Gradient clipping** (max norm=1.0) prevents exploding gradients.
- **Reproducibility**: Fixed seed (42), deterministic cuDNN, config persisted to `checkpoints/training_config.json`.

### 3. Evaluation

```bash
python3 ml/evaluate.py --checkpoint checkpoints/best_model.pth --data_dir data/prepared
```

Outputs:
- `checkpoints/evaluation_metrics.json` — accuracy, F1 (weighted/macro), confusion matrix
- `checkpoints/evaluation_report.txt` — human-readable classification report

### 4. Inference

The backend loads the checkpoint lazily on first request. Each prediction:
1. Breaks the image pair into overlapping 224×224 patches.
2. Runs each patch through the Siamese network.
3. Aggregates patch probabilities for a global prediction.
4. Returns per-patch hotspots with bounding boxes for visualization.

---

## API Reference

### `POST /api/v1/predict`

Upload a pre/post image pair for damage assessment.

**Request:** `multipart/form-data`
| Field | Type | Description |
|---|---|---|
| `pre_image` | File | Pre-disaster satellite image |
| `post_image` | File | Post-disaster satellite image |

**Response:**
```json
{
  "damage_class": "severe-damage",
  "confidence": 0.87,
  "probabilities": {
    "no-damage": 0.05,
    "severe-damage": 0.87,
    "destroyed": 0.08
  },
  "hotspots": [
    {
      "bbox": [112, 0, 224, 224],
      "damage_class": "destroyed",
      "confidence": 0.92
    }
  ],
  "source_dimensions": {
    "width": 1024,
    "height": 1024
  }
}
```

### `GET /api/v1/sample-images`

Returns a base64-encoded sample image pair for demo purposes.

### `GET /health`

Health check endpoint reporting model load status and device info.

### `GET /metrics`

Returns request and prediction metrics (latency, counts, concurrency stats).

---

## Deployment

### Lightweight Profiles (Mac-Friendly)

For resource-constrained machines that struggle with hot-reload and multiple workers:

```bash
# Single-worker backend (no reload)
bash scripts/run_backend_light.sh

# Production-mode frontend (much lighter than dev)
bash scripts/run_frontend_light.sh
```

### Remote Backend Offloading

Keep the UI local but point to a remote GPU-equipped backend:

```bash
BACKEND_ORIGIN=https://your-gpu-server.example.com bash scripts/run_frontend_light.sh
```

Or with the stack helper:

```bash
START_LOCAL_BACKEND=0 BACKEND_ORIGIN=https://your-gpu-server.example.com \
  bash scripts/start_lightweight_stack.sh
```

---

## Quality Assurance

### Frontend

```bash
cd frontend
npm run lint --silent   # ESLint checks
npm run build           # TypeScript compilation + Next.js build
```

### Python

```bash
# Static compile checks
find backend/app ml -type f -name "*.py" -print0 | xargs -0 python3 -m py_compile
python3 -m py_compile backend/test.py test_ds.py

# Backend unit tests
python3 backend/test.py
```

### Artifact Cleanup

```bash
bash scripts/cleanup_artifacts.sh          # Remove caches
bash scripts/cleanup_artifacts.sh --all-generated  # Deeper cleanup
```

> **Note:** This does not remove `data/raw/`, `data/prepared/`, or model checkpoints by default.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<div align="center">

**Built with ❤️ for disaster response**

</div>
]]>
