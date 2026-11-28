"""Postgres storage (DATABASE_URL). Runs only when TEST_DATABASE_URL points to a throwaway database."""
import os
import uuid

import pytest

import backend.db as db

TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not TEST_URL, reason="set TEST_DATABASE_URL to run the Postgres tests")


@pytest.fixture
def pg(monkeypatch):
    schema = f"dysscan_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(db, "DATABASE_URL", TEST_URL)
    monkeypatch.setattr(db, "_SCHEMA", schema)
    monkeypatch.setattr(db, "_PG_READY", set())
    yield
    with db._pg_connect() as conn:
        conn.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def test_session_round_trip(pg):
    sid = db.new_session("HS01")
    db.save_model_a(sid, {"speed_mean": 0.1}, 1, meta={"score": 0.7, "quality": {"valid": True}})
    db.save_model_b(sid, 9.5, 40.1, 0, 0.2)
    db.save_prediction(sid, 1, 0, 1, "majority_vote (tie -> avg prob)")

    s = db.get_session(sid)
    assert s["patient_id"] == "HS01"
    assert s["model_a"]["output"] == 1
    assert s["model_a"]["features_json"] == {"speed_mean": 0.1}
    assert s["model_a"]["meta"]["score"] == 0.7
    assert s["model_b"]["probability"] == 0.2
    assert s["prediction"]["final_output"] == 1

    h = db.get_history()
    assert h[0]["session_id"] == sid
    assert h[0]["model_a_valid"] is True
    assert h[0]["model_b_output"] == 0


def test_history_newest_first_and_missing_b(pg):
    first = db.new_session("HS01")
    db.save_prediction(first, 0, None, 0, "majority_vote (majority)")
    second = db.new_session("HS02")
    db.save_prediction(second, 1, None, 1, "majority_vote (majority)")
    h = db.get_history()
    assert [r["session_id"] for r in h] == [second, first]
    assert h[0]["model_b_output"] is None


def test_import_csv_skips_existing_rows(pg, tmp_path):
    (tmp_path / "sessions.csv").write_text(
        "session_id,patient_id,created_at\nold-1,HS09,2026-11-25T09:20:55\n", encoding="utf-8")
    (tmp_path / "predictions.csv").write_text(
        "prediction_id,session_id,model_a_output,model_b_output,final_output,ensemble_method,predicted_at\n"
        "p-1,old-1,0,,0,majority_vote (majority),2026-11-25T09:20:55\n", encoding="utf-8")
    assert db.import_csv(tmp_path) == {"sessions": 1, "predictions": 1}
    assert db.import_csv(tmp_path) == {"sessions": 0, "predictions": 0}
    assert db.get_history()[0]["patient_id"] == "HS09"


def test_tables_have_row_level_security(pg):
    db.new_session("HS01")
    with db._pg_connect() as conn:
        rls = conn.execute(
            "SELECT c.relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relname = 'sessions'", [db._SCHEMA]).fetchone()
    assert rls == (True,)
