# FastAPI + Next.js Migration — Design

**Date:** 2026-09-17
**Scope:** Replace the Streamlit UI with a Next.js dark clinical dashboard and a FastAPI backend. Preserve the existing ML pipeline untouched under `backend/ml/`. Vietnamese UI.

## Frozen decisions

- Vietnamese UI copy.
- Restructure in place: existing ML Python modules physically move to `backend/ml/`.
- Model B runtime: **ONNX Runtime primary** (`resnet50_backbone.onnx` + two-input `model_b.onnx`, sigmoid verified baked in) with **PyTorch fallback** (`weights/model_b.pt`).
- Model B handcrafted-feature scaling: **apply the stored 2-value scaler** (`model_b_scaler_mean.npy`/`scale.npy`: mean `[9.34700908, 48.02069093]`, scale `[4.08691571, 35.18571286]`) to `[ink_thickness_mean, baseline_deviation]` before feeding the head; **document** that this was inferred from the `.npy` files, not confirmed from a training script.
- Live camera: browser-side `@mediapipe/hands@0.4` (CDN, same approach as `live_cam_component/index.html`); browser collects `(T,21,3)` landmarks and submits them as JSON.
- Single persisting endpoint `POST /api/screening` with a `model_a_source` field (`video` | `live`). `POST /api/screening/model-a` and `model-b` are non-persisting programmatic endpoints.
- Backend runs on system Python 3.11.9. `mediapipe==0.10.14` is the only missing dependency.

## Backend layout

```
backend/
  main.py              # app factory, CORS, exception handlers
  config.py            # repo-root paths, model ids, USE_MODEL_B_SCALER
  schemas.py           # Pydantic response models
  routes/screening.py  # POST /api/screening, /api/screening/model-a, /model-b
  routes/history.py    # GET /api/history, /api/history/{session_id}
  services/model_a_service.py
  services/model_b_service.py
  services/ensemble_service.py
  ml/                  # moved existing modules, unchanged logic
  db.py                # CSV persistence (4 files), + get_session()
  tests/
```

## Frontend layout

```
frontend/
  app/screening/page.tsx       # landing
  app/results/[id]/page.tsx
  app/history/page.tsx
  app/about/page.tsx           # only page exposing technical details
  components/  lib/api.ts  types/  globals.css (theme tokens)
```

## API response shape

`POST /api/screening` returns:
```json
{
  "session_id": "...",
  "patient_id": "patient_001",
  "model_a": { "available": true, "prediction": 1, "score": 0.78,
               "status": "OK", "quality": { "valid": true, "frames": 200,
               "fps": 30, "duration": 6.7 }, "features": { ... } },
  "model_b": { "available": true, "prediction": 1, "score": 0.64 },
  "ensemble": { "prediction": 1, "method": "majority_vote" },
  "disclaimer": "Kết quả sàng lọc, không phải chẩn đoán y tế."
}
```
No filesystem paths, weight filenames, or internal implementation details in any patient-facing response.

## Persistence

4 CSV files under `data/` unchanged (`sessions.csv`, `model_a_features.csv`, `model_b_features.csv`, `predictions.csv`). `db.py` keeps signatures, resolves `DATA_DIR` from the repo root, adds `get_session(session_id)`.

## Ensemble

Exact replication of current `app.py:205-216`: majority vote; tie → average probability with threshold 0.5; Model B absent → Model A decides.

## Theme tokens

- Background `#0B1020`, surface `#131A2B`, border `rgba(148,163,184,0.15)`
- Primary text `#F5F7FA`, secondary muted `#8B93A7`
- Accent blue-violet `#6D7BFF`
- Amber `#F5B544`, red `#EF4444`, green `#34D399`
- No gradients, no glassmorphism, no unnecessary animations.