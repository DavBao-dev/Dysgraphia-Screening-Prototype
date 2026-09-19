# FastAPI + Next.js Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit UI with a Next.js + Tailwind dark clinical dashboard and a FastAPI backend, preserving the existing dysgraphia ML pipeline unchanged under `backend/ml/`.

**Architecture:** Browser collects input (video file OR live-camera landmarks + optional handwriting image) → `POST /api/screening` (multipart) → FastAPI → Model A service (MediaPipe + Random Forest via existing modules), Model B service (ONNX Runtime primary, PyTorch fallback), ensemble service (majority vote) → CSV persistence via `db.py` → structured JSON + `session_id`; results page fetches `GET /api/history/{session_id}`.

**Tech Stack:** FastAPI + uvicorn + pydantic + onnxruntime (Python 3.11.9), Next.js App Router + TypeScript + Tailwind; existing torch/torchvision/scikit-learn/mediapipe==0.10.14; node v26/npm 11.

**Spec:** docs/superpowers/specs/2026-09-17-fastapi-nextjs-migration-design.md

## Global Constraints

- Vietnamese UI copy.
- Restructure in place: existing ML modules move to `backend/ml/` with **no logic changes**; only imports/paths adapt.
- Model B: ONNX Runtime primary (`resnet50_backbone.onnx` → `[1,2048,1,1]` reshaped to `[1,2048]`; `model_b.onnx` inputs `embedding` + `handcrafted`; output `score` already sigmoid, ≥0.5 → 1). PyTorch fallback = `inference.run_model_b`.
- Scaler applied to the 2 handcrafted features: `(x - mean) / scale`, mean=`[9.34700908, 48.02069093]`, scale=`[4.08691571, 35.18571286]`. Document the inference (no training script exists in repo). Feature order fixed: `[ink_thickness_mean, baseline_deviation]`.
- 4 CSV files under `data/` unchanged; `db.py` signatures kept; new `get_session(id)`.
- API responses never expose filesystem paths or weight filenames.
- Frontend: no gradients, glassmorphism, or unnecessary animations; no red as primary; blue-violet accent; tokens in spec.
- Single persisting endpoint is `POST /api/screening`; `/api/screening/model-a` and `model-b` do not persist.
- No git commits until the user explicitly requests them.
- Backend runs on system Python 3.11.9; `mediapipe==0.10.14` must be installed.

---

### Task 1: Backend scaffold (config, schemas, main, requirements)

**Files:**
- Create: `backend/__init__.py`, `backend/config.py`, `backend/schemas.py`, `backend/main.py`, `backend/routes/__init__.py`, `backend/routes/screening.py`, `backend/routes/history.py`, `backend/services/__init__.py`
- Modify: `requirements.txt`
- Test: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `backend.config` constants; `backend.schemas.{ScreeningResponse,ModelAResult,ModelBResult,Quality,EnsembleResult}`; `backend.main.app`; `GET /api/health`.

- [ ] **Step 1: Create package skeleton + `config.py`**

```python
# backend/config.py
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WEIGHTS_DIR = REPO_ROOT / "weights"
DATA_DIR = REPO_ROOT / "data"

MODEL_A_WEIGHTS = WEIGHTS_DIR / "writesense_model_a.joblib"
MODEL_B_BACKBONE_ONNX = WEIGHTS_DIR / "resnet50_backbone.onnx"
MODEL_B_HEAD_ONNX = WEIGHTS_DIR / "model_b.onnx"
MODEL_B_HEAD_TORCH = WEIGHTS_DIR / "model_b.pt"
MODEL_B_SCALER_MEAN = WEIGHTS_DIR / "model_b_scaler_mean.npy"
MODEL_B_SCALER_SCALE = WEIGHTS_DIR / "model_b_scaler_scale.npy"

USE_MODEL_B_SCALER = True
MIN_MODEL_A_FRAMES = 15
MODEL_A_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mpeg4", ".mkv"}
MODEL_B_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
DISCLAIMER = "Kết quả sàng lọc, không phải chẩn đoán y tế."
```

- [ ] **Step 2: Create `schemas.py`**

```python
# backend/schemas.py
from typing import Any, Optional

from pydantic import BaseModel


class Quality(BaseModel):
    valid: bool
    fps: Optional[float] = None
    frames: Optional[int] = None
    duration: Optional[float] = None


class ModelAResult(BaseModel):
    available: bool
    prediction: Optional[int] = None
    score: Optional[float] = None
    status: Optional[str] = None
    quality: Optional[Quality] = None
    features: Optional[dict[str, Any]] = None


class ModelBResult(BaseModel):
    available: bool
    prediction: Optional[int] = None
    score: Optional[float] = None


class EnsembleResult(BaseModel):
    prediction: Optional[int] = None
    method: str


class ScreeningResponse(BaseModel):
    session_id: Optional[str] = None
    patient_id: str
    model_a: Optional[ModelAResult] = None
    model_b: Optional[ModelBResult] = None
    ensemble: Optional[EnsembleResult] = None
    disclaimer: str = "Kết quả sàng lọc, không phải chẩn đoán y tế."
```

- [ ] **Step 3: Create `main.py` (CORS + health + exception handlers)**

```python
# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routes import history, screening

app = FastAPI(title="Dysgraphia Screening API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(screening.router)
app.include_router(history.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "models": {"model_a": True, "model_b": True}}


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Lỗi máy chủ nội bộ."})
```

- [ ] **Step 4: Stub routers** — `backend/routes/screening.py` and `backend/routes/history.py` each containing `router = APIRouter(prefix="/api")` (full bodies come in Task 6).

- [ ] **Step 5: Rewrite `requirements.txt`**

```
pandas>=2.0
numpy>=1.24
opencv-python-headless>=4.9
opencv-contrib-python-headless>=4.9
torch>=2.0
torchvision>=0.15
pillow>=10.0
mediapipe==0.10.14
scipy>=1.10.0
scikit-learn>=1.3
fastapi>=0.110
uvicorn>=0.29
python-multipart>=0.0.9
onnxruntime>=1.18
# openvino>=2024.0  # tùy chọn tăng tốc; không bắt buộc
```

- [ ] **Step 6: Install mediapipe**

Run: `python -m pip install "mediapipe==0.10.14"`
Expected: success; `python -c "import mediapipe; print(mediapipe.__version__)"` prints `0.10.14`.

- [ ] **Step 7: Write + run health test**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["models"]["model_a"] is True
```

Run: `python -m pytest backend/tests/test_health.py -v` → PASS.

---

### Task 2: Move existing ML modules + db.py into `backend/`

**Files:**
- Move (git mv) from repo root → `backend/ml/`: `model_a_dysgraphia.py`, `model_a_adapter.py`, `dysgraphia_predictor.py`, `inference.py`, `inference_openvino.py`, `image_features.py`
- Move (git mv): `db.py` → `backend/db.py`; `test_kinematic_extractor.py` → `backend/tests/`
- Modify: `backend/ml/model_a_adapter.py` (imports), `backend/db.py` (DATA_DIR + `get_session`), `backend/tests/test_kinematic_extractor.py` (imports)

**Interfaces:**
- Produces: `backend.ml.*` modules (imports fixed), `backend.db`.

- [ ] **Step 1: Move modules**

```bash
mkdir -p backend/ml backend/tests
git mv model_a_dysgraphia.py backend/ml/model_a_dysgraphia.py
git mv model_a_adapter.py backend/ml/model_a_adapter.py
git mv dysgraphia_predictor.py backend/ml/dysgraphia_predictor.py
git mv inference.py backend/ml/inference.py
git mv inference_openvino.py backend/ml/inference_openvino.py
git mv image_features.py backend/ml/image_features.py
git mv db.py backend/db.py
git mv test_kinematic_extractor.py backend/tests/test_kinematic_extractor.py
```

Add empty `backend/ml/__init__.py`.

- [ ] **Step 2: Fix imports in `backend/ml/model_a_adapter.py`**

Replace its top-level import with:
```python
from backend.ml.model_a_dysgraphia import KinematicFeatureExtractor, EnhancedKinematicFeatureExtractor
```

- [ ] **Step 3: Fix `backend/db.py`** — replace the `DATA_DIR` line with `from backend.config import DATA_DIR` and add `get_session`:

```python
def get_session(session_id: str) -> dict | None:
    """Trả về chi tiết một phiên (sessions + model_a + model_b + prediction)."""
    sessions = {r["session_id"]: r for r in _read_rows("sessions")}
    if session_id not in sessions:
        return None
    a_rows = [r for r in _read_rows("model_a_features") if r["session_id"] == session_id]
    b_rows = [r for r in _read_rows("model_b_features") if r["session_id"] == session_id]
    p_rows = [r for r in _read_rows("predictions") if r["session_id"] == session_id]
    a = a_rows[-1] if a_rows else None
    b = b_rows[-1] if b_rows else None
    p = p_rows[-1] if p_rows else None
    return {
        "session_id": session_id,
        "patient_id": sessions[session_id].get("patient_id", ""),
        "created_at": sessions[session_id].get("created_at", ""),
        "model_a": {
            "output": _to_int_or_none(a["model_a_output"]) if a else None,
            "features_json": json.loads(a["features_json"]) if a else None,
        },
        "model_b": {
            "output": _to_int_or_none(b["model_b_output"]) if b else None,
            "probability": float(b["model_b_probability"]) if b and b.get("model_b_probability") not in (None, "") else None,
            "ink_thickness_mean": float(b["ink_thickness_mean"]) if b else None,
            "baseline_deviation": float(b["baseline_deviation"]) if b else None,
        },
        "prediction": {
            "final_output": _to_int_or_none(p["final_output"]) if p else None,
            "model_a_output": _to_int_or_none(p["model_a_output"]) if p else None,
            "model_b_output": _to_int_or_none(p["model_b_output"]) if p else None,
            "ensemble_method": p.get("ensemble_method", "") if p else "",
            "predicted_at": p.get("predicted_at", "") if p else "",
        },
    }
```

- [ ] **Step 4: Fix `backend/tests/test_kinematic_extractor.py` imports**

Change `from model_a_dysgraphia import ...` → `from backend.ml.model_a_dysgraphia import ...` and `from dysgraphia_predictor import ...` → `from backend.ml.dysgraphia_predictor import ...`.

- [ ] **Step 5: Run the moved tests**

Run: `python -m pytest backend/tests/test_kinematic_extractor.py -v` → PASS.

---

### Task 3: Model A service

**Files:**
- Create: `backend/services/model_a_service.py`
- Test: `backend/tests/test_model_a_service.py`

**Interfaces:**
- Consumes: `backend.ml.model_a_adapter.extract_landmarks_from_video`, `backend.ml.dysgraphia_predictor.DysgraphiaPredictor`.
- Produces: `run_model_a_video(video_bytes, suffix=".mp4") -> dict`; `run_model_a_landmarks(landmarks, fps) -> dict`. Result keys: `available, prediction, score, status, quality{fps,frames,duration,valid}, features`. Raises `ValueError` on no hand / too few frames / bad shape.

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_model_a_service.py
import numpy as np
import pytest

from backend.services.model_a_service import run_model_a_landmarks


def _writing_landmarks() -> list:
    T = 60
    t = np.linspace(0.0, 1.0, T)
    kp = np.zeros((T, 21, 3), dtype=np.float64)
    kp[:, 0, :] = [0.5, 0.5, 0.0]
    kp[:, 4, :] = [0.55, 0.55, 0.0]
    kp[:, 8, 0] = 0.5 + 0.15 * np.sin(2 * np.pi * t)
    kp[:, 8, 1] = 0.5 + 0.10 * np.sin(4 * np.pi * t)
    for j in range(21):
        if j not in (0, 4, 8):
            kp[:, j, :] = [0.5 + 0.01 * j, 0.5, 0.0]
    return kp.tolist()


def test_model_a_landmarks_returns_valid_result():
    res = run_model_a_landmarks(_writing_landmarks(), fps=30.0)
    assert res["available"] is True
    assert res["prediction"] in (0, 1)
    assert 0.0 <= res["score"] <= 1.0
    assert res["status"] == "OK"
    assert res["quality"]["valid"] is True
    assert res["quality"]["frames"] == 60
    assert res["quality"]["fps"] == 30.0
    assert abs(res["quality"]["duration"] - 2.0) < 1e-6


def test_model_a_too_few_frames_raises():
    bad = [[[0.5] * 3] * 21] * 5
    with pytest.raises(ValueError):
        run_model_a_landmarks(bad, fps=30.0)
```

- [ ] **Step 2: Run tests → expect FAIL** (`pytest backend/tests/test_model_a_service.py -v`).

- [ ] **Step 3: Implement**

```python
# backend/services/model_a_service.py
import os
import tempfile
from functools import lru_cache

import numpy as np

from backend.config import MIN_MODEL_A_FRAMES, MODEL_A_WEIGHTS
from backend.ml import model_a_adapter
from backend.ml.dysgraphia_predictor import DysgraphiaPredictor


@lru_cache(maxsize=1)
def _predictor() -> DysgraphiaPredictor:
    return DysgraphiaPredictor.load(str(MODEL_A_WEIGHTS))


def _build_result(pred_res, frames: int, fps: float) -> dict:
    status = pred_res["status"]
    return {
        "available": True,
        "prediction": 1 if pred_res["risk_score"] >= 0.5 else 0,
        "score": float(pred_res["risk_score"]),
        "status": status,
        "quality": {
            "valid": status == "OK",
            "fps": float(fps),
            "frames": int(frames),
            "duration": round(frames / fps, 3),
        },
        "features": pred_res["features"],
    }


def run_model_a_video(video_bytes: bytes, suffix: str = ".mp4") -> dict:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    try:
        trajectory, fps = model_a_adapter.extract_landmarks_from_video(tmp_path)
    finally:
        os.unlink(tmp_path)
    if trajectory.shape[0] < MIN_MODEL_A_FRAMES:
        raise ValueError(
            f"Không đủ dữ liệu: cần >= {MIN_MODEL_A_FRAMES} frame có bàn tay, "
            f"chỉ nhận được {trajectory.shape[0]} frame."
        )
    return _build_result(_predictor().predict_kinematics(trajectory, fps=fps), trajectory.shape[0], fps)


def run_model_a_landmarks(landmarks, fps: float) -> dict:
    arr = np.asarray(landmarks, dtype=np.float64)
    if arr.ndim != 3 or arr.shape[1:] != (21, 3):
        raise ValueError(f"Landmarks phải có shape (T,21,3), nhận được {arr.shape}.")
    if arr.shape[0] < MIN_MODEL_A_FRAMES:
        raise ValueError(
            f"Không đủ frame có bàn tay: cần >= {MIN_MODEL_A_FRAMES}, nhận được {arr.shape[0]}."
        )
    return _build_result(_predictor().predict_kinematics(arr, fps=fps), arr.shape[0], fps)
```

- [ ] **Step 4: Run tests → expect PASS.**---

### Task 4: Model B service (ONNX primary + scaler + torch fallback)

**Files:**
- Create: `backend/services/model_b_service.py`
- Test: `backend/tests/test_model_b_service.py`

**Interfaces:**
- Consumes: `backend.ml.image_features.extract_ink_and_baseline_features`, `backend.ml.inference` (`_IMAGENET_TRANSFORM`, `load_resnet50_backbone`, `load_model_b_head`, `run_model_b`), `backend.config`.
- Produces: `run_model_b_image(image_bytes) -> dict` keys `available, prediction, score`; `last_features() -> dict` (raw handcrafted values of the most recent call).

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_model_b_service.py
import io

import numpy as np
from PIL import Image

from backend.services import model_b_service


def _make_handwriting_image() -> bytes:
    d = np.zeros((256, 256), dtype=np.uint8)
    d[80:120, 60:200] = 30
    d[130:170, 60:180] = 40
    buf = io.BytesIO()
    Image.fromarray(d).save(buf, format="PNG")
    return buf.getvalue()


def test_model_b_image_returns_valid_result():
    res = model_b_service.run_model_b_image(_make_handwriting_image())
    assert res["available"] is True
    assert res["prediction"] in (0, 1)
    assert 0.0 <= res["score"] <= 1.0


def test_model_b_invalid_image_raises():
    try:
        model_b_service.run_model_b_image(b"not an image")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_scaler_formula():
    from backend.config import MODEL_B_SCALER_MEAN, MODEL_B_SCALER_SCALE
    import numpy as np
    mean = np.load(MODEL_B_SCALER_MEAN)
    scale = np.load(MODEL_B_SCALER_SCALE)
    assert mean.shape == (2,) and scale.shape == (2,)
    x = np.array([9.34700908, 48.02069093])
    assert np.allclose((x - mean) / scale, 0.0, atol=1e-5)
```

Note: the invalid-image test relies on `image_features` raising `ValueError` (it does: "Khong doc duoc anh").

- [ ] **Step 2: Run tests → expect FAIL.**

- [ ] **Step 3: Implement `model_b_service.py` (scaler inference documented in docstring)**

```python
# backend/services/model_b_service.py
"""Model B — ảnh chữ viết → embedding ResNet50 (ONNX) + 2 feature thủ công → MLP head.

Đường dẫn mặc định: ONNX Runtime (`resnet50_backbone.onnx` + `model_b.onnx`),
fallback PyTorch (`weights/model_b.pt`).

LƯU Ý SCALER: `model_b_scaler_mean.npy` / `model_b_scaler_scale.npy` lưu đúng 2
giá trị (mean ≈ [9.35, 48.02], scale ≈ [4.09, 35.19]) khớp với 2 feature thủ công
[ink_thickness_mean, baseline_deviation]. Ta GIẢ ĐỊNH 2 feature này được chuẩn hóa
bằng StandardScaler trước khi vào head lúc training — suy luận từ shape/giá trị file,
KHÔNG có training script trong repo để xác nhận. Nếu có script gốc hãy đối chiếu.
"""
import io
from functools import lru_cache

import numpy as np

from backend.config import (
    MODEL_B_BACKBONE_ONNX,
    MODEL_B_HEAD_TORCH,
    MODEL_B_SCALER_MEAN,
    MODEL_B_SCALER_SCALE,
    USE_MODEL_B_SCALER,
)
from backend.ml import image_features
from backend.ml.inference import _IMAGENET_TRANSFORM

MODEL_B_HEAD_ONNX = None  # resolved lazily via config in _sessions()

_last = {}


@lru_cache(maxsize=1)
def _onnx_inputs():
    # Re-import to keep module import light; sessions are cached process-wide.
    from backend.config import MODEL_B_HEAD_ONNX as HEAD

    import onnxruntime as ort

    return (
        ort.InferenceSession(str(MODEL_B_BACKBONE_ONNX), providers=["CPUExecutionProvider"]),
        ort.InferenceSession(str(HEAD), providers=["CPUExecutionProvider"]),
    ), HEAD


def _scaler():
    mean = np.load(MODEL_B_SCALER_MEAN).astype(np.float32)
    scale = np.load(MODEL_B_SCALER_SCALE).astype(np.float32)
    return mean, scale


def last_features() -> dict:
    return dict(_last)


def run_model_b_image(image_bytes: bytes) -> dict:
    feats = image_features.extract_ink_and_baseline_features(image_bytes)
    _last.clear()
    _last.update(feats)

    hc = np.array([feats["ink_thickness_mean"], feats["baseline_deviation"]], dtype=np.float32)
    if USE_MODEL_B_SCALER:
        mean, scale = _scaler()
        hc = (hc - mean) / scale

    try:
        score = _run_onnx(image_bytes, hc)
    except Exception:
        score = _run_torch(image_bytes, hc)

    return {"available": True, "prediction": 1 if score >= 0.5 else 0, "score": round(float(score), 6)}


def _run_onnx(image_bytes: bytes, hc: np.ndarray) -> float:
    from PIL import Image

    (backbone, head) = _onnx_inputs()[0]
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    t = _IMAGENET_TRANSFORM(pil).unsqueeze(0).numpy().astype(np.float32)  # (1,3,224,224)
    emb = np.asarray(backbone.run(None, {"image": t})[0]).reshape(1, 2048).astype(np.float32)
    out = head.run(None, {"embedding": emb, "handcrafted": hc.reshape(1, 2)})[0]
    return float(np.asarray(out).reshape(-1)[0])


def _run_torch(image_bytes: bytes, hc: np.ndarray) -> float:
    from backend.ml import inference

    head_path = str(inference_import_helper())
    backbone = inference.load_resnet50_backbone()
    head = inference.load_model_b_head(head_path)
    _, prob = inference.run_model_b(backbone, head, image_bytes, extra_features=hc.tolist())
    return float(prob)


def inference_import_helper():
    from backend.config import MODEL_B_HEAD_TORCH

    return MODEL_B_HEAD_TORCH
```

- [ ] **Step 4: Run tests → expect PASS** (first ONNX eval loads the 94 MB backbone; allow extra time).

- [ ] **Step 5: Add ONNX≈torch consistency test** (only if ONNX works; tolerance 1e-2)

```python
def test_onnx_torch_consistency():
    img = _make_handwriting_image()
    a = model_b_service._run_onnx(img, np.zeros(2, dtype=np.float32))
    b = model_b_service._run_torch(img, np.zeros(2, dtype=np.float32))
    assert abs(a - b) < 1e-2
```

Run: `python -m pytest backend/tests/test_model_b_service.py -v` → PASS.

---

### Task 5: Ensemble service

**Files:**
- Create: `backend/services/ensemble_service.py`
- Test: `backend/tests/test_ensemble_service.py`

**Interfaces:**
- Produces: `combine(model_a: dict | None, model_b: dict | None) -> dict` with keys `prediction` (int) and `method` (str). Raises `ValueError` when both are None.

- [ ] **Step 1: Write failing tests (replicate current `app.py:205-216` voting)**

```python
# backend/tests/test_ensemble_service.py
from backend.services.ensemble_service import combine

A1 = {"prediction": 1, "score": 0.9}
A0 = {"prediction": 0, "score": 0.1}
B1 = {"prediction": 1, "score": 0.8}
B0 = {"prediction": 0, "score": 0.2}


def test_agree_uses_common_result():
    assert combine(A1, B1) == {"prediction": 1, "method": "majority_vote (majority)"}


def test_disagree_uses_probabilities():
    res = combine(A1, B0)
    assert res["method"] == "majority_vote (tie -> avg prob)"
    assert res["prediction"] == 1  # avg(0.9, 0.2) = 0.55 >= 0.5


def test_model_b_absent_model_a_decides():
    assert combine(A1, None) == {"prediction": 1, "method": "majority_vote (majority)"}


def test_both_absent_raises():
    try:
        combine(None, None)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run → expect FAIL.**

- [ ] **Step 3: Implement, mirroring `app.py:205-216`**

```python
# backend/services/ensemble_service.py
def combine(model_a, model_b):
    if model_a is None and model_b is None:
        raise ValueError("Không có mô hình nào có kết quả để tổng hợp.")
    out_a = model_a["prediction"] if model_a else None
    prob_a = model_a["score"] if model_a else None
    out_b = model_b["prediction"] if model_b else None
    prob_b = model_b["score"] if model_b else None

    outputs = [(o, p) for o, p in ((out_a, prob_a), (out_b, prob_b)) if o is not None]
    ones = sum(1 for o, _ in outputs if o == 1)
    zeros = sum(1 for o, _ in outputs if o == 0)
    if ones > zeros:
        final_out, vote_kind = 1, "majority"
    elif zeros > ones:
        final_out, vote_kind = 0, "majority"
    else:
        probs = [p for _, p in outputs if p is not None]
        avg = sum(probs) / len(probs) if probs else 0.5
        final_out, vote_kind = (1 if avg >= 0.5 else 0), "tie -> avg prob"
    return {"prediction": final_out, "method": f"majority_vote ({vote_kind})"}
```

- [ ] **Step 4: Run → expect PASS.**

---

### Task 6: FastAPI routes (screening + history) and persistence wiring

**Files:**
- Modify: `backend/routes/screening.py`, `backend/routes/history.py`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: services (Tasks 3–5), `backend.db`, `backend.schemas`.
- Produces: `POST /api/screening`, `POST /api/screening/model-a`, `POST /api/screening/model-b`, `GET /api/history`, `GET /api/history/{session_id}`.

- [ ] **Step 1: Write failing API tests**

```python
# backend/tests/test_api.py
import io
import json

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app

client = TestClient(app)


def _landmarks_json() -> str:
    T = 60
    t = np.linspace(0.0, 1.0, T)
    kp = np.zeros((T, 21, 3), dtype=np.float64)
    kp[:, 0, :] = [0.5, 0.5, 0.0]
    kp[:, 4, :] = [0.55, 0.55, 0.0]
    kp[:, 8, 0] = 0.5 + 0.15 * np.sin(2 * np.pi * t)
    kp[:, 8, 1] = 0.5 + 0.10 * np.sin(4 * np.pi * t)
    for j in range(21):
        if j not in (0, 4, 8):
            kp[:, j, :] = [0.5 + 0.01 * j, 0.5, 0.0]
    return json.dumps({"landmarks": kp.tolist(), "fps": 30.0})


def _image_bytes() -> bytes:
    d = np.zeros((256, 256), dtype=np.uint8)
    d[80:120, 60:200] = 30
    buf = io.BytesIO()
    Image.fromarray(d).save(buf, format="PNG")
    return buf.getvalue()


def test_screening_live_with_image_ends_to_end():
    r = client.post(
        "/api/screening",
        data={"patient_id": "patient_001", "model_a_source": "live", "landmarks_json": _landmarks_json()},
        files={"image": ("hw.png", _image_bytes(), "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["session_id"]
    assert body["patient_id"] == "patient_001"
    assert body["model_a"]["available"] is True
    assert body["model_b"]["available"] is True
    assert body["model_b"]["prediction"] in (0, 1)
    assert body["ensemble"]["prediction"] in (0, 1)
    assert "Kết quả sàng lọc" in body["disclaimer"]
    detail = client.get(f"/api/history/{body['session_id']}")
    assert detail.status_code == 200
    assert detail.json()["patient_id"] == "patient_001"


def test_screening_live_without_image_model_b_absent():
    r = client.post(
        "/api/screening",
        data={"patient_id": "p2", "model_a_source": "live", "landmarks_json": _landmarks_json()},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["model_b"]["available"] is False
    assert body["ensemble"]["prediction"] == body["model_a"]["prediction"]


def test_screening_requires_model_a_input():
    r = client.post("/api/screening", data={"patient_id": "p3", "model_a_source": "video"})
    assert r.status_code == 400


def test_screening_bad_landmarks_returns_400():
    r = client.post(
        "/api/screening",
        data={"patient_id": "p4", "model_a_source": "live", "landmarks_json": json.dumps({"landmarks": [], "fps": 30})},
    )
    assert r.status_code == 400


def test_history_list():
    r = client.get("/api/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_history_missing_session_404():
    assert client.get("/api/history/nope").status_code == 404
```

- [ ] **Step 2: Run → expect FAIL.**

- [ ] **Step 3: Implement `routes/screening.py`**

```python
# backend/routes/screening.py
import json
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

import backend.db as db
from backend import schemas
from backend.config import DISCLAIMER, MODEL_A_VIDEO_EXTS, MODEL_B_IMAGE_EXTS
from backend.services import ensemble_service, model_a_service, model_b_service

router = APIRouter(prefix="/api")


def _ext(name: Optional[str]) -> str:
    if not name or "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1].lower()


@router.post("/screening", response_model=schemas.ScreeningResponse)
def run_screening(
    patient_id: str = Form("patient_001"),
    model_a_source: str = Form("video"),
    video: Optional[UploadFile] = File(None),
    landmarks_json: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    if model_a_source not in {"video", "live"}:
        raise ValueError("model_a_source phải là 'video' hoặc 'live'.")

    if model_a_source == "video":
        if video is None:
            raise ValueError("Cần upload video cho Model A.")
        if _ext(video.filename) not in MODEL_A_VIDEO_EXTS:
            raise ValueError("Định dạng video không hỗ trợ (MP4/MOV/AVI/MPEG4).")
        model_a = model_a_service.run_model_a_video(video.file.read(), suffix=_ext(video.filename))
    else:
        if not landmarks_json:
            raise ValueError("Live camera: cần chuỗi landmark.")
        try:
            payload = json.loads(landmarks_json)
        except json.JSONDecodeError:
            raise ValueError("landmarks_json không hợp lệ.")
        model_a = model_a_service.run_model_a_landmarks(
            payload.get("landmarks"), float(payload.get("fps", 30.0))
        )

    model_b = None
    if image is not None:
        if _ext(image.filename) not in MODEL_B_IMAGE_EXTS:
            raise ValueError("Định dạng ảnh không hỗ trợ (PNG/JPG/JPEG).")
        model_b = model_b_service.run_model_b_image(image.file.read())

    ensemble = ensemble_service.combine(model_a, model_b)

    session_id = db.new_session(patient_id)
    db.save_model_a(session_id, model_a["features"], model_a["prediction"],
                    note="Model A: Random Forest (writesense)")
    if model_b is not None:
        feats = model_b_service.last_features()
        db.save_model_b(session_id, feats["ink_thickness_mean"], feats["baseline_deviation"],
                        model_b["prediction"], model_b["score"])
    db.save_prediction(session_id, model_a["prediction"],
                       model_b["prediction"] if model_b else None,
                       ensemble["prediction"], ensemble["method"])

    return schemas.ScreeningResponse(
        session_id=session_id,
        patient_id=patient_id,
        model_a=model_a,
        model_b=model_b or {"available": False, "prediction": None, "score": None},
        ensemble=ensemble,
        disclaimer=DISCLAIMER,
    )


@router.post("/screening/model-a", response_model=schemas.ModelAResult)
def run_model_a_only(
    model_a_source: str = Form("video"),
    video: Optional[UploadFile] = File(None),
    landmarks_json: Optional[str] = Form(None),
):
    if model_a_source not in {"video", "live"}:
        raise ValueError("model_a_source phải là 'video' hoặc 'live'.")
    if model_a_source == "video":
        if video is None:
            raise ValueError("Cần upload video cho Model A.")
        return model_a_service.run_model_a_video(video.file.read(), suffix=_ext(video.filename))
    if not landmarks_json:
        raise ValueError("Live camera: cần chuỗi landmark.")
    payload = json.loads(landmarks_json)
    return model_a_service.run_model_a_landmarks(payload.get("landmarks"), float(payload.get("fps", 30.0)))


@router.post("/screening/model-b", response_model=schemas.ModelBResult)
def run_model_b_only(image: UploadFile = File(...)):
    if _ext(image.filename) not in MODEL_B_IMAGE_EXTS:
        raise ValueError("Cần upload ảnh PNG/JPG/JPEG cho Model B.")
    return model_b_service.run_model_b_image(image.file.read())
```

- [ ] **Step 4: Implement `routes/history.py`**

```python
# backend/routes/history.py
from fastapi import APIRouter, HTTPException

import backend.db as db
from backend.config import DISCLAIMER

router = APIRouter(prefix="/api")


@router.get("/history")
def history(limit: int = 50):
    return db.get_history(limit=limit)


@router.get("/history/{session_id}")
def history_detail(session_id: str):
    d = db.get_session(session_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên.")
    a, b, p = d["model_a"], d["model_b"], d["prediction"]
    return {
        "session_id": session_id,
        "patient_id": d["patient_id"],
        "created_at": d["created_at"],
        "model_a": {
            "available": True,
            "prediction": a["output"],
            "score": None,
            "status": None,
            "quality": None,
            "features": a["features_json"] or {},
        },
        "model_b": {
            "available": b["output"] is not None,
            "prediction": b["output"],
            "score": b["probability"],
            "handcrafted": {
                "ink_thickness_mean": b["ink_thickness_mean"],
                "baseline_deviation": b["baseline_deviation"],
            },
        },
        "ensemble": {"prediction": p["final_output"], "method": p["ensemble_method"]},
        "disclaimer": DISCLAIMER,
    }
```

- [ ] **Step 5: Run API tests → expect PASS.**
---

### Task 7: Frontend scaffold (create-next-app + theme)

**Files:**
- Create: full `frontend/` via `create-next-app`
- Modify: `frontend/app/globals.css`, `frontend/next.config.ts`, `frontend/lib/api.ts`, `frontend/types/screening.ts`

**Interfaces:**
- Consumes: API from Tasks 1–6.
- Produces: Next.js app with Tailwind; `lib/api.ts` (`runScreening`, `getHistory`, `getSession`); `types/screening.ts` types.

- [ ] **Step 1: Scaffold**

Run inside repo root:
```bash
npx create-next-app@latest frontend --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --no-git --use-npm --turbopack
```
Answer prompts with defaults (no src-dir → app at `frontend/app/`). Then `npm run dev` works on :3000. If `--src-dir` chosen, paths below use `frontend/src/app/`; adjust accordingly.

- [ ] **Step 2: Define theme tokens in `globals.css`** — dark navy/charcoal, no gradients/glass:

```css
@import "tailwindcss";

:root {
  --bg: #0B1020;
  --surface: #131A2B;
  --surface-2: #1A2236;
  --border: rgba(148, 163, 184, 0.15);
  --text: #F5F7FA;
  --muted: #8B93A7;
  --accent: #6D7BFF;
  --accent-2: #4F7CFF;
  --amber: #F5B544;
  --red: #EF4444;
  --green: #34D399;
}

@media (prefers-color-scheme: light) { :root { --bg:#fff; --surface:#f7f8fb; } }
```
In a Tailwind v4 setup, register tokens:
```css
@theme inline {
  --color-background: var(--bg);
  --color-surface: var(--surface);
  ...
}
```
then use `bg-background`, `bg-surface`, `text-muted`, `border-border`, `bg-accent`, etc.

- [ ] **Step 3: `lib/api.ts`** — all calls go to `/api/*` (dev rewrites in `next.config.ts`):

```ts
// frontend/lib/api.ts
import type { HealthResponse, HistoryRow, ScreeningResponse, SessionDetail } from "@/types/screening";

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Lỗi máy chủ." }));
    throw new Error(body.detail ?? "Lỗi máy chủ.");
  }
  return res.json() as Promise<T>;
}

export function runScreening(form: FormData): Promise<ScreeningResponse> {
  return j(fetch("/api/screening", { method: "POST", body: form }));
}
export function getHistory(): Promise<HistoryRow[]> {
  return j(fetch("/api/history"));
}
export function getSession(id: string): Promise<SessionDetail> {
  return j(fetch(`/api/history/${id}`));
}
export function getHealth(): Promise<HealthResponse> {
  return j(fetch("/api/health"));
}
```

- [ ] **Step 4: `types/screening.ts`** — mirror backend schemas:

```ts
export interface Quality { valid: boolean; fps?: number | null; frames?: number | null; duration?: number | null; }
export interface ModelAResult { available: boolean; prediction: number | null; score: number | null; status: string | null; quality: Quality | null; features: Record<string, number> | null; }
export interface ModelBResult { available: boolean; prediction: number | null; score: number | null; handcrafted?: { ink_thickness_mean: number; baseline_deviation: number }; }
export interface EnsembleResult { prediction: number; method: string; }
export interface ScreeningResponse { session_id: string | null; patient_id: string; model_a: ModelAResult; model_b: ModelBResult; ensemble: EnsembleResult; disclaimer: string; }
export interface SessionDetail extends ScreeningResponse { created_at: string; }
export interface HistoryRow { predicted_at: string; session_id: string; patient_id: string; model_a_output: number | null; model_b_output: number | null; final_output: number | null; ensemble_method: string; }
export interface HealthResponse { status: string; models: { model_a: boolean; model_b: boolean }; }
```

- [ ] **Step 5: Dev rewrites in `next.config.ts`**

```ts
const nextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" }];
  },
};
export default nextConfig;
```

- [ ] **Step 6: Verify build** — `npm run build` succeeds.

---

### Task 8: Frontend — screening page

**Files:**
- Create: `frontend/app/page.tsx` (redirect → `/screening`), `frontend/app/screening/page.tsx`, `frontend/components/Header.tsx`, `frontend/components/Dropzone.tsx`, `frontend/components/VideoPanel.tsx`, `frontend/components/LiveCamera.tsx`, `frontend/components/HandwritingPanel.tsx`, `frontend/components/RunButton.tsx`, `frontend/components/PatientInput.tsx`

**Interfaces:**
- Consumes: `lib/api.ts`, types.
- Produces: the screening workflow page (cards 01/02, tabs, dropzones, live camera, run action → navigates to `/results/{session_id}`).

- [ ] **Step 1: Header + global layout** — left: title "Dysgraphia Screening" + subtitle; right: "Sàng lọc mới" button (also nav links: Lịch sử, Thông tin mô hình).

- [ ] **Step 2: Screening page structure**

- `patient_id` editable text input default `patient_001` (top, Patient section).
- Card **01 Chuyển động tay** — badge "Bắt buộc"; segmented control `Upload video` / `Camera trực tiếp`.
- Card **02 Chữ viết tay** — badge "Tùy chọn"; caption "Thêm mô hình thứ hai vào quá trình sàng lọc"; dropzone PNG/JPG/JPEG with preview + remove/replace.
- Bottom: `RunButton` "Chạy sàng lọc" — disabled until Model A valid; caption "Phân tích chữ viết là tùy chọn".
- On submit: build `FormData`:
  - `patient_id`, `model_a_source: video|live`
  - video source → append `video` File
  - live source → append `landmarks_json` = `JSON.stringify({ landmarks, fps })`
  - optional image → append `image` File
  - calls `runScreening(form)`, on success `router.push("/results/" + session_id)`.

- [ ] **Step 3: `Dropzone.tsx`** — hand-rolled: click-to-browse + drag-over styling; props `accept`, `onFile(file)`, `value` (name/size), `onRemove`; shows filename, size (MB), duration (video metadata via `<video>` or object URL), remove button.

- [ ] **Step 4: `VideoPanel.tsx`** — tab state; upload mode uses `Dropzone` with accepts `.mp4,.mov,.avi,.mpeg4`; live mode renders `LiveCamera` and shows captured frame count + a hint when `<15` frames captured.

- [ ] **Step 5: `LiveCamera.tsx`** — client component that loads the same CDN MediaPipe Hands 0.4 scripts used by `live_cam_component/index.html`, renders video + canvas with drawn landmarks, buffers `[t,21,3]` arrays, computes median FPS, exposes `start/stop/retake`, and calls `onResult({ landmarks, fps })`. Buttons: "Bắt đầu ghi" / "Dừng ghi" / "Quay lại".

- [ ] **Step 6: `HandwritingPanel.tsx`** — `Dropzone` accepts `.png,.jpg,.jpeg`; image preview via object URL; remove/replace.

- [ ] **Step 7: `RunButton.tsx`** — disabled when invalid; error toast/banner on API errors; loading state "Đang phân tích...".

---

### Task 9: Frontend — results, history, about pages

**Files:**
- Create: `frontend/app/results/[id]/page.tsx`, `frontend/app/history/page.tsx`, `frontend/app/about/page.tsx`, `frontend/components/StatusCard.tsx`, `frontend/components/FeatureGroups.tsx`, `frontend/components/ModelCard.tsx`

**Interfaces:**
- Consumes: `lib/api.ts`, types, theme.

- [ ] **Step 1: Results page** — `useParams` → `getSession(id)`; header "Kết quả sàng lọc / Bệnh nhân {patient_id} / {created_at formatted}". Main card **Tín hiệu sàng lọc**: "Tăng cao" (accent border) vs "Không nổi bật", always with disclaimer caption. Then model cards:
  - **Chuyển động tay — Model A**: score, "Prediction: Elevated signal"/"Thấp" (neutral text "Tín hiệu tăng cao"/"Không nổi bật"), quality line (fps/duration) if present.
  - **Chữ viết — Model B**: score + prediction; if `!available` → "Không được phân tích" + caption "Không cung cấp ảnh tùy chọn".
  - **Ensemble**: "Các mô hình nhất trí" (Models agree) or tie text + method.
- **Detailed analysis** sections (collapsible `<details>`): Model A feature groups (Movement / Tremor / Coordination) using `FeatureGroups.tsx`, and Model B handcrafted features labeled "Model features (không phải đo lường lâm sàng)".

- [ ] **Step 2: `FeatureGroups.tsx`** — group Model A feature keys:

```ts
const GROUPS: Record<string, string[]> = {
  "Chuyển động": ["speed_mean","speed_max","speed_std","acceleration_mean",
    "acceleration_max","acceleration_std","jerk_mean","jerk_max","jerk_std",
    "mean_speed","std_speed","mean_jerk","max_jerk","normalized_jerk",
    "nvc_per_second","in_air_pause_ratio"],
  "Run tay": ["tremor_peak_frequency_hz","tremor_peak_amplitude",
    "spectral_entropy","tremor_power_ratio"],
  "Phối hợp": ["wrist_flexion_angle_mean","wrist_flexion_angle_std",
    "pinch_distance_std","pinch_distance_mean","pincer_correlation","wrist_drift_rate"],
};
```
Renders each group as a small table (label maps + formatted values). Unknown keys go into a "Khác" group. Advanced detail fold-out lists all raw features.

- [ ] **Step 3: History page** — table (Bệnh nhân / Thời gian / Mô hình A / Mô hình B / Kết quả), rows clickable → `/results/{session_id}`.

- [ ] **Step 4: About page** — "Thông tin mô hình" only page exposing technical detail: Model A (video/live → MediaPipe → Random Forest), Model B (ảnh → ResNet50 embedding + 2 feature thủ công → MLP), ensemble; disclaimer; link to README. No weight paths.

---

### Task 10: E2E verification, cleanup, README

**Files:**
- Modify: `README.md`, `.gitignore`
- Delete: `app.py`, `live_camera.py`, `live_cam_component/` (replaced)
- Verify: `python -m pytest`, `npm run lint`, `npm run build`, live server e2e

**Interfaces:** — none new.

- [ ] **Step 1: Run full backend suite** — `python -m pytest backend/tests -v` → all PASS (including moved tests + new services + API).

- [ ] **Step 2: Frontend checks** — `npm run lint` and `npm run build` → clean.

- [ ] **Step 3: Live end-to-end** — start backend `python -m uvicorn backend.main:app --port 8000`, start frontend `npm run dev`, then:
  1. `GET /api/health` → ok.
  2. `POST /api/screening` with `model_a_source=live` and a synthetic landmarks JSON (helper script `backend/tests/helpers.py` or curl) + an optional PNG → returns `session_id`; check `data/predictions.csv` gained a row.
  3. Open `http://localhost:3000/screening`, upload a real video + image, run → navigate to results; confirm Model A/B/Ensemble cards.
  4. Live camera flow: record → run → results.
  5. History page shows the new rows.

- [ ] **Step 4: Cleanup**
- Delete `app.py`, `live_camera.py`, `live_cam_component/index.html` (+ dir) — Streamlit UI replaced.
- Remove `streamlit` from requirements (done in Task 1).
- Update `.gitignore`: keep `data/`, add `weights/resnet50_openvino.{xml,bin}`, `backend/__pycache__` etc.

- [ ] **Step 5: README** — document: run backend (`pip install -r requirements.txt`; `uvicorn backend.main:app --reload`), run frontend (`npm install; npm run dev`), API table (all 6 routes), ML pipeline (Model A/B + ensemble + scaler note + ONNX path), legacy unused weights inventory (do not delete): `resnet50_backbone_openvino.*`, `model_b_openvino*.{xml,bin}`, note `app.py` removed. State the scaler assumption clearly.

---

### Task 11: Final review

- [ ] **Step 1:** Re-read full plan + spec; confirm every spec section has a task.
- [ ] **Step 2:** `git status` clean of stray files; no weight deletions.
