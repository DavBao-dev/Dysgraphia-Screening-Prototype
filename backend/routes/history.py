# backend/routes/history.py
from fastapi import APIRouter, HTTPException

import backend.db as db
from backend.config import DISCLAIMER

router = APIRouter(prefix="/api")


@router.get("/history")
def history(limit: int = 50):
    return db.get_history(limit=limit)


@router.get("/history/{session_id}")
def history_detail(session_id: str):
    d = db.get_session(session_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên.")
    a, b, p = d["model_a"], d["model_b"], d["prediction"]
    return {
        "session_id": session_id,
        "patient_id": d["patient_id"],
        "created_at": d["created_at"],
        "model_a": {
            "available": True,
            "prediction": a["output"],
            "score": None,
            "status": None,
            "quality": None,
            "features": a["features_json"] or {},
        },
        "model_b": {
            "available": b["output"] is not None,
            "prediction": b["output"],
            "score": b["probability"],
            "handcrafted": {
                "ink_thickness_mean": b["ink_thickness_mean"],
                "baseline_deviation": b["baseline_deviation"],
            },
        },
        "ensemble": {"prediction": p["final_output"], "method": p["ensemble_method"]},
        "disclaimer": DISCLAIMER,
    }
