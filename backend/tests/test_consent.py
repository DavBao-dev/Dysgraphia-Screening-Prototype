import ast
import time
from pathlib import Path
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from backend import consent

@pytest.fixture
def setup(monkeypatch):
    for k,v in {"CONSENT_PRIVATE_ACCESS_VERIFIED":"true", "CONSENT_SUPABASE_STORAGE_VERIFIED":"true", "CONSENT_APP_LOCATION":"Private application server, Singapore", "CONSENT_SIGNING_KEY":"a"*48,"SUPABASE_URL":"https://example.supabase.co","SUPABASE_SERVICE_ROLE_KEY":"test-server-only"}.items():
        monkeypatch.setenv(k,v)
    evidence=[]
    monkeypatch.setattr(consent,"_audit",lambda record: evidence.append(record))
    app=FastAPI();app.include_router(consent.router)
    @app.post("/process")
    def process(receipt_id=Depends(consent.require_consent)):
        return {"receipt_id":receipt_id}
    return TestClient(app),evidence

def payload():
    p=consent.policy()
    return {"version":p["version"],"policy_hash":p["policy_hash"],"role":"parent","accepted":True,"child_assent":True,"authority_confirmed":True}

def test_missing_configuration_blocks_acceptance(setup,monkeypatch):
    client,records=setup;monkeypatch.delenv("CONSENT_SUPABASE_STORAGE_VERIFIED")
    assert client.get("/api/consent/policy").json()["ready"] is False
    assert client.post("/api/consent",json=payload()).status_code==503
    assert client.post("/process").status_code==503
    assert records==[]

@pytest.mark.parametrize("field",["accepted","child_assent","authority_confirmed"])
def test_each_confirmation_is_required(setup,field):
    client,records=setup;body=payload();body[field]=False
    assert client.post("/api/consent",json=body).status_code==403
    assert records==[]

def test_teacher_requires_separate_guardian_reference(setup):
    client,records=setup;body=payload();body["role"]="teacher"
    assert client.post("/api/consent",json=body).status_code==400
    body["guardian_reference"]="CONSENT-TEST-001"
    assert client.post("/api/consent",json=body).status_code==200
    assert records[0]["guardian_reference"]=="CONSENT-TEST-001"

def test_valid_receipt_is_bound_to_document_and_expiry(setup,monkeypatch):
    client,records=setup
    accepted=client.post("/api/consent",json=payload()).json();token=accepted["token"]
    assert len(records)==1 and records[0]["document"]["sections"]==consent.policy()["sections"]
    assert records[0]["purpose"]=="screening" and records[0]["accepted_at"].endswith("+00:00")
    assert client.post("/process",headers={"X-Consent-Token":token}).json()["receipt_id"]==accepted["receipt_id"]
    assert client.post("/process").status_code==403
    assert client.post("/process",headers={"X-Consent-Token":token+"x"}).status_code==403
    monkeypatch.setenv("CONSENT_APP_LOCATION","Changed provider")
    assert client.post("/process",headers={"X-Consent-Token":token}).status_code==403

def test_outdated_terms_and_expired_tokens_rejected(setup,monkeypatch):
    client,_=setup;body=payload();body["version"]="old"
    assert client.post("/api/consent",json=body).status_code==409
    accepted=client.post("/api/consent",json=payload()).json()
    later=time.time()+5*3600;monkeypatch.setattr(consent.time,"time",lambda:later)
    assert client.post("/process",headers={"X-Consent-Token":accepted["token"]}).status_code==403

def test_evidence_failure_does_not_issue_receipt(setup,monkeypatch):
    from fastapi import HTTPException
    client,_=setup
    def fail(record): raise HTTPException(503,"Store unavailable")
    monkeypatch.setattr(consent,"_audit",fail)
    assert client.post("/api/consent",json=payload()).status_code==503

def test_all_three_analysis_routes_require_consent():
    tree=ast.parse((Path(__file__).parents[1]/"routes"/"screening.py").read_text(encoding="utf-8"))
    functions={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
    for name in ["run_screening","run_model_a_only","run_model_b_only"]:
        assert any(isinstance(default,ast.Call) and ast.unparse(default)=="Depends(require_consent)" for default in functions[name].args.defaults)
