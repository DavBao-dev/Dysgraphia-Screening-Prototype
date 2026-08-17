"""
inference_openvino.py - Tang toc Model B (ResNet50 backbone) bang OpenVINO.

Chuyen doi ResNet50 (PyTorch, ImageNet pretrained, bo lop fc) sang OpenVINO IR
(cache vao weights/resnet50_openvino.{xml,bin}) roi chay embedding 2048-d bang
OpenVINO runtime (nhanh hon tren CPU Intel). MLP head van chay bang PyTorch.

Neu OpenVINO khong san co (chua cai, loi convert...), app.py nen fallback ve
inference.py (PyTorch thuan).
"""
import io
import os

import numpy as np
import torch
from PIL import Image
from torchvision import models as tv_models

from inference import DEVICE, _IMAGENET_TRANSFORM

WEIGHTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")
IR_XML = os.path.join(WEIGHTS_DIR, "resnet50_openvino.xml")
IR_BIN = os.path.join(WEIGHTS_DIR, "resnet50_openvino.bin")


def convert_resnet50_to_ir() -> str:
    """Chuyen ResNet50 -> OpenVINO IR, luu cache. Tra ve duong dan XML."""
    import openvino as ov
    import torch.nn as nn

    resnet = tv_models.resnet50(weights=tv_models.ResNet50_Weights.IMAGENET1K_V2)
    resnet.fc = nn.Identity()  # bo lop phan loai, giu embedding 2048-d
    resnet.eval()
    example = torch.randn(1, 3, 224, 224)
    ov_model = ov.convert_model(resnet, example_input=example)
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    ov.save_model(ov_model, IR_XML)
    return IR_XML


def load_resnet50_openvino():
    """Tra ve OpenVINO CompiledModel (convert cache neu chua co)."""
    import openvino as ov

    core = ov.Core()
    if not (os.path.exists(IR_XML) and os.path.exists(IR_BIN)):
        convert_resnet50_to_ir()
    try:
        return core.compile_model(IR_XML, "CPU")
    except Exception:
        convert_resnet50_to_ir()  # cache loi/cu -> convert lai
        return core.compile_model(IR_XML, "CPU")


def embedding_from_image(compiled, image_bytes: bytes) -> np.ndarray:
    """Anh -> embedding ResNet50 (2048,) bang OpenVINO."""
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    t = _IMAGENET_TRANSFORM(pil).unsqueeze(0)  # (1,3,224,224)
    arr = t.numpy().astype(np.float32)
    result = compiled(arr)
    return np.asarray(result[compiled.output(0)]).reshape(-1)  # (2048,)


def run_model_b(compiled, head, image_bytes: bytes, extra_features):
    """OpenVINO embedding + MLP head (PyTorch) -> (pred, prob)."""
    emb = embedding_from_image(compiled, image_bytes)
    combined = np.concatenate([emb, np.asarray(extra_features, dtype=np.float32)])  # (2050,)
    t = torch.from_numpy(combined).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        logit = head(t)
        prob = torch.sigmoid(logit).item()
        pred = 1 if prob >= 0.5 else 0
    return pred, prob
