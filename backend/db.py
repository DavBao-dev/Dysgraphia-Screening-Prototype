"""
db.py - Luu ket qua chan doan vao file CSV (thay cho MySQL/SQLite).

Moi "bang" cua MySQL cu duoc thay bang 1 file CSV trong thu muc data/:

    data/sessions.csv           - session_id, patient_id, created_at
    data/model_a_features.csv   - feature_id, session_id, features_json, model_a_output, model_a_note
    data/model_b_features.csv   - feature_id, session_id, ink_thickness_mean, baseline_deviation, model_b_output, model_b_probability
    data/predictions.csv        - prediction_id, session_id, model_a_output, model_b_output, final_output, ensemble_method, predicted_at

Giu nguyen ten ham + signature nhu ban MySQL de backend FastAPI khong phai sua.

Neu dat bien moi truong DATABASE_URL (Postgres, vd. Supabase), 4 "bang" tren duoc luu vao schema
"dysscan" cua database do thay vi CSV: cung ten cot, gia tri luu dang text giong het cell CSV, nen
phan doc ben duoi khong doi. Bat Row Level Security de API cong khai cua Supabase khong doc duoc.
Chep du lieu CSV cu len database:  python -m backend.db import-csv
"""
import csv
import json
import os
import sys
import threading
import uuid
from datetime import datetime

from backend.config import DATA_DIR, DATABASE_URL

_SCHEMA = "dysscan"

# Lock de ghi file an toan khi backend FastAPI xu ly nhieu request cung luc
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


def _cell(value) -> str:
    """Gia tri nhu csv.writer ghi ra: None -> "", con lai -> str()."""
    return "" if value is None else str(value)


# ------------------------------------------------------------------ Postgres (khi co DATABASE_URL)
_PG_READY = set()


def _pg_connect():
    import psycopg

    # prepare_threshold=None: khong dung prepared statement, chay duoc qua pooler cua Supabase.
    return psycopg.connect(DATABASE_URL, autocommit=True, prepare_threshold=None)


def _pg_table(name: str):
    from psycopg import sql

    return sql.Identifier(_SCHEMA, name)


def _pg_ensure_table(name: str) -> None:
    if name in _PG_READY:
        return
    from psycopg import sql

    cols = sql.SQL(", ").join(sql.SQL("{} text NOT NULL DEFAULT ''").format(sql.Identifier(f)) for f in _FILES[name]["fields"])
    with _pg_connect() as conn:
        conn.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(_SCHEMA)))
        # _row giu thu tu ghi, giong thu tu dong trong file CSV.
        conn.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} (_row bigserial PRIMARY KEY, {})").format(_pg_table(name), cols))
        conn.execute(sql.SQL("ALTER TABLE {} ENABLE ROW LEVEL SECURITY").format(_pg_table(name)))
    _PG_READY.add(name)


def _pg_append_row(name: str, values: dict) -> None:
    from psycopg import sql

    _pg_ensure_table(name)
    fields = _FILES[name]["fields"]
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        _pg_table(name),
        sql.SQL(", ").join(map(sql.Identifier, fields)),
        sql.SQL(", ").join(sql.Placeholder() * len(fields)),
    )
    with _pg_connect() as conn:
        conn.execute(query, [_cell(values.get(f)) for f in fields])


def _pg_read_rows(name: str) -> list:
    from psycopg import sql
    from psycopg.rows import dict_row

    _pg_ensure_table(name)
    fields = _FILES[name]["fields"]
    query = sql.SQL("SELECT {} FROM {} ORDER BY _row").format(sql.SQL(", ").join(map(sql.Identifier, fields)), _pg_table(name))
    with _pg_connect() as conn:
        return conn.cursor(row_factory=dict_row).execute(query).fetchall()


# ------------------------------------------------------------------ CSV (mac dinh)
def _ensure_table(name: str) -> None:
    """Tao file CSV + dong header neu file chua ton tai."""
    if DATABASE_URL:
        return _pg_ensure_table(name)
    spec = _FILES[name]
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(spec["path"]):
        with open(spec["path"], "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(spec["fields"])


def _append_row(name: str, values: dict) -> None:
    """Ghi them 1 dong moi vao cuoi file CSV (thread-safe)."""
    if DATABASE_URL:
        return _pg_append_row(name, values)
    spec = _FILES[name]
    _ensure_table(name)
    row = [values.get(field, "") for field in spec["fields"]]
    with _LOCK:
        with open(spec["path"], "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)


def _read_rows(name: str) -> list:
    """Doc toan bo cac dong cua 1 file CSV (tru header)."""
    if DATABASE_URL:
        return _pg_read_rows(name)
    spec = _FILES[name]
    _ensure_table(name)
    with open(spec["path"], "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def import_csv(data_dir=DATA_DIR) -> dict:
    """Chep cac dong trong file CSV cu len database (bo qua dong co id da ton tai). Tra ve so dong da chep."""
    if not DATABASE_URL:
        raise RuntimeError("Chua dat DATABASE_URL.")
    copied = {}
    for name, spec in _FILES.items():
        path = os.path.join(data_dir, os.path.basename(spec["path"]))
        if not os.path.exists(path):
            continue
        id_field = spec["fields"][0]
        existing = {r[id_field] for r in _pg_read_rows(name)}
        with open(path, "r", newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r.get(id_field) not in existing]
        for r in rows:
            _pg_append_row(name, r)
        copied[name] = len(rows)
    return copied


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


def save_model_a(session_id: str, features: dict, output=None, note: str = "", meta: dict | None = None):
    """Luu cac features (JSON) va ket qua cua Model A.

    `meta` (diem, trang thai, chat luong video) duoc ghi dang JSON vao cot model_a_note, de khong phai
    doi cau truc file CSV; cac dong cu chi co ghi chu thuong (khong phai JSON) van doc duoc.
    """
    _append_row("model_a_features", {
        "feature_id": str(uuid.uuid4()),
        "session_id": session_id,
        "features_json": json.dumps(features),
        "model_a_output": output,
        "model_a_note": json.dumps(meta, ensure_ascii=False) if meta is not None else note,
    })


def _meta_from_note(note) -> dict | None:
    """Doc lai `meta` da luu trong model_a_note; None neu day la ghi chu thuong cua ban ghi cu."""
    try:
        meta = json.loads(note) if note else None
    except (TypeError, ValueError):
        return None
    return meta if isinstance(meta, dict) else None


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

    # Chat luong video cua Model A (da luu trong meta); None voi ban ghi cu khong co meta.
    valid_by_session = {}
    for a in _read_rows("model_a_features"):
        quality = (_meta_from_note(a.get("model_a_note")) or {}).get("quality") or {}
        valid_by_session[a["session_id"]] = quality.get("valid")

    rows = []
    for p in reversed(_read_rows("predictions")):  # moi nhat truoc
        rows.append({
            "model_a_valid": valid_by_session.get(p["session_id"]),
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


def get_session(session_id: str) -> dict | None:
    """Trả về chi tiết một phiên (sessions + model_a + model_b + prediction)."""
    sessions = {r["session_id"]: r for r in _read_rows("sessions")}
    if session_id not in sessions:
        return None
    a_rows = [r for r in _read_rows("model_a_features") if r["session_id"] == session_id]
    b_rows = [r for r in _read_rows("model_b_features") if r["session_id"] == session_id]
    p_rows = [r for r in _read_rows("predictions") if r["session_id"] == session_id]
    a = a_rows[-1] if a_rows else None
    b = b_rows[-1] if b_rows else None
    p = p_rows[-1] if p_rows else None
    return {
        "session_id": session_id,
        "patient_id": sessions[session_id].get("patient_id", ""),
        "created_at": sessions[session_id].get("created_at", ""),
        "model_a": {
            "output": _to_int_or_none(a["model_a_output"]) if a else None,
            "features_json": json.loads(a["features_json"]) if a else None,
            "meta": _meta_from_note(a.get("model_a_note")) if a else None,
        },
        "model_b": {
            "output": _to_int_or_none(b["model_b_output"]) if b else None,
            "probability": float(b["model_b_probability"]) if b and b.get("model_b_probability") not in (None, "") else None,
            "ink_thickness_mean": float(b["ink_thickness_mean"]) if b else None,
            "baseline_deviation": float(b["baseline_deviation"]) if b else None,
        },
        "prediction": {
            "final_output": _to_int_or_none(p["final_output"]) if p else None,
            "model_a_output": _to_int_or_none(p["model_a_output"]) if p else None,
            "model_b_output": _to_int_or_none(p["model_b_output"]) if p else None,
            "ensemble_method": p.get("ensemble_method", "") if p else "",
            "predicted_at": p.get("predicted_at", "") if p else "",
        },
    }


if __name__ == "__main__":
    if sys.argv[1:] == ["import-csv"]:
        print(import_csv())
    else:
        print("Dung: python -m backend.db import-csv")
