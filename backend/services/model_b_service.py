"""Model B — ảnh chữ viết → embedding ResNet50 (ONNX) + 2 feature thủ công → MLP head.

Đường dẫn mặc định: ONNX Runtime (`resnet50_backbone.onnx` + `model_b.onnx`),
fallback PyTorch (`weights/model_b.pt`).

Trọng số, scaler và pipeline này được tạo bởi `train_model_b.py` ở gốc repo:
ảnh → `image_features.normalize_handwriting` (mực đen trên nền trắng) → 2 feature
thủ công [ink_thickness_mean, baseline_deviation] chuẩn hóa bằng StandardScaler
(`model_b_scaler_mean.npy` / `model_b_scaler_scale.npy`) + embedding ResNet50 →
MLP head. Sửa bước nào ở đây thì phải chạy lại `train_model_b.py`.
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
    image_bytes = image_features.normalize_handwriting(image_bytes)
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


def extract_embedding(image_bytes: bytes) -> np.ndarray:
    """Embedding ResNet50 (ONNX) 2048-d, shape (1, 2048). Dùng chung cho app và train_model_b.py."""
    from PIL import Image

    backbone = _onnx_inputs()[0][0]
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    t = _IMAGENET_TRANSFORM(pil).unsqueeze(0).numpy().astype(np.float32)  # (1,3,224,224)
    return np.asarray(backbone.run(None, {"image": t})[0]).reshape(1, 2048).astype(np.float32)


def _run_onnx(image_bytes: bytes, hc: np.ndarray) -> float:
    head = _onnx_inputs()[0][1]
    emb = extract_embedding(image_bytes)
    out = head.run(None, {"embedding": emb, "handcrafted": hc.reshape(1, 2).astype(np.float32)})[0]
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