"""
db.py - Luu ket qua chan doan vao file CSV (thay cho MySQL/SQLite).

Moi "bang" cua MySQL cu duoc thay bang 1 file CSV trong thu muc data/:

    data/sessions.csv           - session_id, patient_id, created_at
    data/model_a_features.csv   - feature_id, session_id, features_json, model_a_output, model_a_note
    data/model_b_features.csv   - feature_id, session_id, ink_thickness_mean, baseline_deviation, model_b_output, model_b_probability
    data/predictions.csv        - prediction_id, session_id, model_a_output, model_b_output, final_output, ensemble_method, predicted_at

Giu nguyen ten ham + signature nhu ban MySQL de app.py khong can sua gi.
"""
import csv
import json
import os
import threading
import uuid
from datetime import datetime

# Thu muc chua cac file CSV (tu dong tao neu chua co)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Lock de ghi file an toan khi Streamlit chay nhieu session cung luc
_LOCK = threading.Lock()

_FILES = {
    "sessions": {
        "path": os.path.join(DATA_DIR, "sessions.csv"),
        "fields": ["session_id", "patient_id", "created_at"],
    },
    "model_a_features": {
        "path": os.path.join(DATA_DIR, "model_a_features.csv"),
        "fields": ["feature_id", "session_id", "features_json", "model_a_output", "model_a_note"],
    },
    "model_b_features": {
        "path": os.path.join(DATA_DIR, "model_b_features.csv"),
        "fields": ["feature_id", "session_id", "ink_thickness_mean", "baseline_deviation", "model_b_output", "model_b_probability"],
    },
    "predictions": {
        "path": os.path.join(DATA_DIR, "predictions.csv"),
        "fields": ["prediction_id", "session_id", "model_a_output", "model_b_output", "final_output", "ensemble_method", "predicted_at"],
    },
}


def _ensure_table(name: str) -> None:
    """Tao file CSV + dong header neu file chua ton tai."""
    spec = _FILES[name]
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(spec["path"]):
        with open(spec["path"], "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(spec["fields"])


def _append_row(name: str, values: dict) -> None:
    """Ghi them 1 dong moi vao cuoi file CSV (thread-safe)."""
    spec = _FILES[name]
    _ensure_table(name)
    row = [values.get(field, "") for field in spec["fields"]]
    with _LOCK:
        with open(spec["path"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)


def _read_rows(name: str) -> list:
    """Doc toan bo cac dong cua 1 file CSV (tru header)."""
    spec = _FILES[name]
    _ensure_table(name)
    with open(spec["path"], "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def init_db() -> None:
    """Khoi tao cac file CSV neu chua ton tai."""
    for name in _FILES:
        _ensure_table(name)


def new_session(patient_id: str) -> str:
    """Tao phien lam viec moi cho benh nhan. Tra ve session_id."""
    session_id = str(uuid.uuid4())
    _append_row("sessions", {
        "session_id": session_id,
        "patient_id": patient_id,
        "created_at": datetime.now().isoformat(),
    })
    return session_id


def save_model_a(session_id: str, features: dict, output=None, note: str = ""):
    """Luu cac features (JSON) va ket qua cua Model A."""
    _append_row("model_a_features", {
        "feature_id": str(uuid.uuid4()),
        "session_id": session_id,
        "features_json": json.dumps(features),
        "model_a_output": output,
        "model_a_note": note,
    })


def save_model_b(session_id: str, ink_thickness_mean: float, baseline_deviation: float, output: int, probability: float):
    """Luu cac features va ket qua cua Model B."""
    _append_row("model_b_features", {
        "feature_id": str(uuid.uuid4()),
        "session_id": session_id,
        "ink_thickness_mean": float(ink_thickness_mean),
        "baseline_deviation": float(baseline_deviation),
        "model_b_output": output,
        "model_b_probability": float(probability),
    })


def save_prediction(session_id: str, out_a, out_b, final_out: int, method: str):
    """Luu ket qua du doan cuoi cung (Ensemble)."""
    _append_row("predictions", {
        "prediction_id": str(uuid.uuid4()),
        "session_id": session_id,
        "model_a_output": out_a,
        "model_b_output": out_b,
        "final_output": final_out,
        "ensemble_method": method,
        "predicted_at": datetime.now().isoformat(),
    })


def _to_int_or_none(value):
    """Chuyen cell CSV (string) ve int hoac None de hien thi gon hon."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def get_history(limit: int = 50):
    """Lay lich su du doan moi nhat (join predictions + sessions theo session_id)."""
    patient_by_session = {
        r["session_id"]: r["patient_id"] for r in _read_rows("sessions")
    }

    rows = []
    for p in reversed(_read_rows("predictions")):  # moi nhat truoc
        rows.append({
            "predicted_at": p["predicted_at"],
            "session_id": p["session_id"],
            "patient_id": patient_by_session.get(p["session_id"], ""),
            "model_a_output": _to_int_or_none(p["model_a_output"]),
            "model_b_output": _to_int_or_none(p["model_b_output"]),
            "final_output": _to_int_or_none(p["final_output"]),
            "ensemble_method": p["ensemble_method"],
        })
        if len(rows) >= int(limit):
            break

    return rows
