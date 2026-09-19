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