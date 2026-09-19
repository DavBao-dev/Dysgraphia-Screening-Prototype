# backend/routes/screening.py
import json
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

import backend.db as db
from backend import schemas
from backend.config import DISCLAIMER, MAX_VIDEO_BYTES, MODEL_A_VIDEO_EXTS, MODEL_B_IMAGE_EXTS
from backend.services import ensemble_service, model_a_service, model_b_service

router = APIRouter(prefix="/api")


def _ext(name: Optional[str]) -> str:
    if not name or "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1].lower()


def _run_model_a_video(video: UploadFile) -> dict:
    if _ext(video.filename) not in MODEL_A_VIDEO_EXTS:
        raise ValueError("Định dạng video không hỗ trợ (MP4/MOV/AVI/MPEG4).")
    try:
        return model_a_service.run_model_a_video(
            video.file, suffix=_ext(video.filename), max_bytes=MAX_VIDEO_BYTES, filename=video.filename
        )
    except model_a_service.VideoTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc


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
        model_a = _run_model_a_video(video)
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
        return _run_model_a_video(video)
    if not landmarks_json:
        raise ValueError("Live camera: cần chuỗi landmark.")
    payload = json.loads(landmarks_json)
    return model_a_service.run_model_a_landmarks(payload.get("landmarks"), float(payload.get("fps", 30.0)))


@router.post("/screening/model-b", response_model=schemas.ModelBResult)
def run_model_b_only(image: UploadFile = File(...)):
    if _ext(image.filename) not in MODEL_B_IMAGE_EXTS:
        raise ValueError("Cần upload ảnh PNG/JPG/JPEG cho Model B.")
    return model_b_service.run_model_b_image(image.file.read())

