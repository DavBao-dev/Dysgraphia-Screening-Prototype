# backend/services/model_a_service.py
import logging
import os
import shutil
import tempfile
from functools import lru_cache

import numpy as np

from backend.config import MAX_VIDEO_SIZE_MB, MIN_MODEL_A_FRAMES, MODEL_A_WEIGHTS
from backend.ml import model_a_adapter
from backend.ml.dysgraphia_predictor import DysgraphiaPredictor

logger = logging.getLogger("model_a")


class VideoTooLargeError(ValueError):
    pass


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


def _file_size(fileobj) -> int:
    try:
        pos = fileobj.tell()
        fileobj.seek(0, os.SEEK_END)
        size = fileobj.tell()
        fileobj.seek(pos)
        return size
    except (OSError, ValueError):
        return 0


def run_model_a_video(fileobj, suffix: str = ".mp4", max_bytes: int | None = None, filename: str | None = None) -> dict:
    if max_bytes and _file_size(fileobj) > max_bytes:
        raise VideoTooLargeError(
            f"Video quá lớn. Vui lòng chọn video nhỏ hơn {MAX_VIDEO_SIZE_MB} MB."
        )
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(fileobj, tmp, length=1024 * 256)
        tmp_path = tmp.name
    size = os.path.getsize(tmp_path)
    logger.info("model_a video: filename=%s size=%d bytes temp=%s", filename, size, tmp_path)
    try:
        trajectory, fps = model_a_adapter.extract_landmarks_from_video(tmp_path)
    finally:
        os.unlink(tmp_path)
    if trajectory.shape[0] < MIN_MODEL_A_FRAMES:
        raise ValueError(
            f"Kh\u00f4ng \u0111\u1ee7 d\u1eef li\u1ec7u: c\u1ea7n >= {MIN_MODEL_A_FRAMES} frame c\u00f3 b\u00e0n tay, "
            f"ch\u1ec9 nh\u1eadn \u0111\u01b0\u1ee3c {trajectory.shape[0]} frame."
        )
    logger.info("model_a RF inference: starting frames=%d fps=%.2f", trajectory.shape[0], fps)
    result = _build_result(_predictor().predict_kinematics(trajectory, fps=fps), trajectory.shape[0], fps)
    logger.info("model_a RF inference: completed")
    return result


def run_model_a_landmarks(landmarks, fps: float) -> dict:
    arr = np.asarray(landmarks, dtype=np.float64)
    if arr.ndim != 3 or arr.shape[1:] != (21, 3):
        raise ValueError(f"Landmarks ph\u1ea3i c\u00f3 shape (T,21,3), nh\u1eadn \u0111\u01b0\u1ee3c {arr.shape}.")
    if arr.shape[0] < MIN_MODEL_A_FRAMES:
        raise ValueError(
            f"Kh\u00f4ng \u0111\u1ee7 frame c\u00f3 b\u00e0n tay: c\u1ea7n >= {MIN_MODEL_A_FRAMES}, nh\u1eadn \u0111\u01b0\u1ee3c {arr.shape[0]}."
        )
    return _build_result(_predictor().predict_kinematics(arr, fps=fps), arr.shape[0], fps)
