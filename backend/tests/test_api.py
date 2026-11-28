# backend/tests/test_api.py
import io
import pytest
import json

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.config import MAX_VIDEO_SIZE_MB

client = TestClient(app)

@pytest.fixture(autouse=True)
def verified_consent_for_model_tests(monkeypatch):
    from backend.consent import require_consent
    import backend.routes.screening as screening
    app.dependency_overrides[require_consent] = lambda: "test-receipt"
    monkeypatch.setattr(screening, "link_session", lambda *_: None)
    yield
    app.dependency_overrides.pop(require_consent, None)



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



def _still_landmarks_json() -> str:
    kp = np.zeros((60, 21, 3), dtype=np.float64)
    for j in range(21):
        kp[:, j, :] = [0.5 + 0.01 * j, 0.5, 0.0]
    return json.dumps({"landmarks": kp.tolist(), "fps": 30.0})


def test_saved_session_keeps_model_a_score_and_quality():
    r = client.post(
        "/api/screening",
        data={"patient_id": "keep1", "model_a_source": "live", "landmarks_json": _landmarks_json()},
    )
    assert r.status_code == 200, r.text
    live = r.json()["model_a"]
    saved = client.get(f"/api/history/{r.json()['session_id']}").json()["model_a"]
    assert saved["score"] == live["score"]
    assert saved["status"] == live["status"]
    assert saved["quality"] == live["quality"]
    assert saved["prediction"] == live["prediction"]


def test_saved_session_of_an_unusable_video_is_marked_invalid():
    r = client.post(
        "/api/screening",
        data={"patient_id": "keep2", "model_a_source": "live", "landmarks_json": _still_landmarks_json()},
    )
    assert r.status_code == 200, r.text
    assert r.json()["model_a"]["quality"]["valid"] is False
    saved = client.get(f"/api/history/{r.json()['session_id']}").json()["model_a"]
    assert saved["quality"]["valid"] is False
    assert saved["status"] == r.json()["model_a"]["status"]


def test_saved_features_do_not_leak_the_stored_meta():
    r = client.post(
        "/api/screening",
        data={"patient_id": "keep3", "model_a_source": "live", "landmarks_json": _landmarks_json()},
    )
    features = client.get(f"/api/history/{r.json()['session_id']}").json()["model_a"]["features"]
    assert features == r.json()["model_a"]["features"]


def test_old_session_without_stored_meta_still_loads():
    import backend.db as db

    sid = db.new_session("old1")
    db.save_model_a(sid, {"speed_mean": 0.1}, 0, note="Model A: Random Forest (writesense)")
    db.save_prediction(sid, 0, None, 0, "majority_vote (majority)")
    saved = client.get(f"/api/history/{sid}").json()["model_a"]
    assert saved["score"] is None and saved["quality"] is None and saved["status"] is None
    assert saved["features"] == {"speed_mean": 0.1}


def _history_row(session_id: str) -> dict:
    return next(r for r in client.get("/api/history?limit=500").json() if r["session_id"] == session_id)


def test_history_list_flags_whether_the_video_was_usable():
    ok = client.post(
        "/api/screening",
        data={"patient_id": "hv1", "model_a_source": "live", "landmarks_json": _landmarks_json()},
    ).json()["session_id"]
    bad = client.post(
        "/api/screening",
        data={"patient_id": "hv2", "model_a_source": "live", "landmarks_json": _still_landmarks_json()},
    ).json()["session_id"]
    assert _history_row(ok)["model_a_valid"] is True
    assert _history_row(bad)["model_a_valid"] is False


def test_history_list_of_an_old_session_has_unknown_video_quality():
    import backend.db as db

    sid = db.new_session("old2")
    db.save_model_a(sid, {"speed_mean": 0.1}, 0, note="Model A: Random Forest (writesense)")
    db.save_prediction(sid, 0, None, 0, "majority_vote (majority)")
    assert _history_row(sid)["model_a_valid"] is None
