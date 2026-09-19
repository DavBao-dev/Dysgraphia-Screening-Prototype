# backend/tests/test_model_a_service.py
import io

import numpy as np
import pytest

from backend.services.model_a_service import VideoTooLargeError, run_model_a_landmarks, run_model_a_video


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


def test_model_a_video_too_large_raises():
    with pytest.raises(VideoTooLargeError):
        run_model_a_video(io.BytesIO(b"x" * 1024), suffix=".mp4", max_bytes=100)


def test_model_a_video_garbage_raises_value_error():
    with pytest.raises(ValueError):
        run_model_a_video(io.BytesIO(b"not-a-real-mp4" * 64), suffix=".mp4")
