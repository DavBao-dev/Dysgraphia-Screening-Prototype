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


def test_onnx_torch_consistency():
    img = _make_handwriting_image()
    a = model_b_service._run_onnx(img, np.zeros(2, dtype=np.float32))
    b = model_b_service._run_torch(img, np.zeros(2, dtype=np.float32))
    assert abs(a - b) < 1e-2