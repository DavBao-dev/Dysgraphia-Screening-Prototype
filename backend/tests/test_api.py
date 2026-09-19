# backend/tests/test_api.py
import io
import json

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.config import MAX_VIDEO_SIZE_MB

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


def test_screening_video_too_large_returns_413(monkeypatch):
    import backend.routes.screening as screening

    monkeypatch.setattr(screening, "MAX_VIDEO_BYTES", 10)
    r = client.post(
        "/api/screening",
        data={"patient_id": "p413", "model_a_source": "video"},
        files={"video": ("big.mp4", b"x" * 100, "video/mp4")},
    )
    assert r.status_code == 413
    assert "Video quá lớn" in r.json()["detail"]
    assert str(MAX_VIDEO_SIZE_MB) in r.json()["detail"]


def test_screening_video_decode_error_returns_400():
    r = client.post(
        "/api/screening",
        data={"patient_id": "pdec", "model_a_source": "video"},
        files={"video": ("bad.mp4", b"not-a-real-mp4" * 64, "video/mp4")},
    )
    assert r.status_code == 400
    assert r.json()["detail"]


def test_history_list():
    r = client.get("/api/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_history_missing_session_404():
    assert client.get("/api/history/nope").status_code == 404

