import pytest
from fastapi.testclient import TestClient

from app import store


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    store.reset(str(tmp_path_factory.mktemp("db") / "test.db"))
    from app.main import app

    return TestClient(app)


def say(client, sid, text=None, payload=None):
    r = client.post(f"/api/advisor/sessions/{sid}/messages", json={"text": text, "payload": payload})
    assert r.status_code == 200, r.text
    return r.json()


def test_free_text_conversation_reaches_recommendation(client):
    s = client.post("/api/advisor/sessions", json={"lang": "en"}).json()
    sid = s["id"]
    r = say(client, sid, "I run a dental clinic in Pune with 8 staff, we use home broadband and pay about Rs 4000 a month")
    p = r["profile"]
    assert p["business_type"] == "Dental clinic" and p["city"] == "Pune" and p["employees"] == 8
    assert p["monthly_spend"] == 4000 and p["segment"] == "prof"
    # remaining: sites, has_gstin, needs
    r = say(client, sid, payload={"set": {"sites": 1}})
    assert r["messages"][-1]["slot"] == "has_gstin"
    r = say(client, sid, "yes")
    assert r["messages"][-1]["slot"] == "needs"
    r = say(client, sid, payload={"set_needs": ["internet", "email", "backup", "security"]})
    assert r["stage"] == "recommended"
    rec = r["recommendation"]
    assert rec["default"] == "recommended"
    ids = {l["product_id"] for l in rec["tiers"]["recommended"]["lines"]}
    assert {"P16", "P17", "P20"} <= ids


def test_hindi_no_gst_kirana(client):
    s = client.post("/api/advisor/sessions", json={"lang": "hi"}).json()
    sid = s["id"]
    r = say(client, sid, "मेरी इंदौर में किराना की दुकान है, 2 लोग काम करते हैं, GST नहीं है")
    p = r["profile"]
    assert p["business_type"] == "Kirana store" and p["city"] == "Indore" and p["has_gstin"] is False
    assert any("ऀ" <= ch <= "ॿ" for ch in r["messages"][-1]["text"])  # replied in Hindi


def test_cancelled_gstin_in_chat_blocks_gst_products(client):
    sid = client.post("/api/advisor/sessions", json={"lang": "en"}).json()["id"]
    say(client, sid, "travel agency in Visakhapatnam, 6 employees, 1 office, mobile hotspot")
    r = say(client, sid, payload={"skip": "monthly_spend"})
    r = say(client, sid, "our GSTIN is 37IHKXV5167L1ZS")
    assert r["profile"]["gstin_status"] == "Cancelled"
    assert any("Cancelled" in m["text"] for m in r["messages"])
    r = say(client, sid, payload={"set_needs": ["internet", "messaging", "telephony"]})
    lines = r["recommendation"]["tiers"]["recommended"]["lines"]
    assert not {l["product_id"] for l in lines} & {"P12", "P14", "P15"}


def test_handoff_request(client):
    sid = client.post("/api/advisor/sessions", json={"lang": "en"}).json()["id"]
    r = say(client, sid, "can someone call me?")
    assert r["stage"] == "handoff"
    q = client.get("/api/backoffice/queue").json()
    assert any(i["id"] == sid and i["reason"] == "asked_for_human" for i in q)


def test_order_rejects_ineligible_bundle(client):
    r = client.post("/api/orders", json={
        "profile": {"segment": "micro", "city_tier": 2, "employees": 2, "sites": 1, "has_gstin": False},
        "items": [{"product_id": "P03", "quantity": 1}], "contract_months": 12})
    assert r.status_code == 422
    codes = {p["code"] for p in r.json()["detail"]["problems"]}
    assert {"city_tier", "needs_gstin", "min_employees"} <= codes


def _order(client, items=None):
    r = client.post("/api/orders", json={
        "profile": {"business_type": "Furniture workshop", "segment": "mfg", "city": "Nagpur", "city_tier": 2,
                    "employees": 12, "sites": 1, "has_gstin": True},
        "items": items or [{"product_id": "P02", "quantity": 1}, {"product_id": "P07", "quantity": 2}],
        "contract_months": 12, "lang": "en"})
    assert r.status_code == 200, r.text
    return r.json()


def test_kyc_requires_consent(client):
    o = _order(client)
    r = client.post(f"/api/orders/{o['id']}/documents/gst_certificate/sample/K03")
    assert r.status_code == 403


@pytest.mark.parametrize("applicant,verdict,failing", [
    ("K03", "verified", set()),
    ("K06", "rejected", {"gstin.checksum"}),
    ("K11", "rejected", {"address.date"}),
])
def test_kyc_end_to_end(client, applicant, verdict, failing):
    o = _order(client)
    oid = o["id"]
    assert client.post(f"/api/orders/{oid}/consent", json={"accepted": True}).status_code == 200
    for slot in ["gst_certificate", "udyam_certificate", "signatory_id", "address_proof"]:
        r = client.post(f"/api/orders/{oid}/documents/{slot}/sample/{applicant}")
        assert r.status_code == 200, r.text
        if "gstin" in r.json()["fields"]:
            assert "•" in r.json()["fields"]["gstin"]  # masked on the way out
    res = client.post(f"/api/orders/{oid}/kyc/verify", json={}).json()
    assert res["verdict"] == verdict
    assert {c["id"] for c in res["checks"] if c["status"] == "fail"} == failing
    status = res["order"]["status"]
    assert status == ("kyc_verified" if verdict == "verified" else "kyc_action_needed")


def test_tracker_progression_and_notifications(client):
    o = _order(client)
    oid = o["id"]
    for _ in range(5):
        client.post(f"/api/backoffice/orders/{oid}/advance", json={})
    t = client.get(f"/api/orders/{oid}").json()["tracker"]
    assert t["status"] == "activated"
    assert len(t["notifications"]) == 6


def test_withdraw_consent_deletes_documents(client):
    o = _order(client)
    oid = o["id"]
    client.post(f"/api/orders/{oid}/consent", json={"accepted": True})
    client.post(f"/api/orders/{oid}/documents/signatory_id/sample/K03")
    client.post(f"/api/orders/{oid}/consent/withdraw")
    assert client.get(f"/api/orders/{oid}").json()["documents"] == {}


def test_insights_and_model(client):
    ins = client.get("/api/backoffice/insights").json()
    assert ins["funnel"][0]["count"] == 5000 and ins["funnel"][-1]["count"] == 368
    assert ins["activated_on_inactive_gstin"] == 22
    assert ins["model"]["auc"] > 0.6


def test_hindi_multisite_answers_do_not_rename_business(client):
    sid = client.post("/api/advisor/sessions", json={"lang": "hi"}).json()["id"]
    r = say(client, sid, "मेरी जयपुर में 3 बेकरी हैं, 14 लोग काम करते हैं")
    assert r["profile"]["sites"] == 3 and r["profile"]["segment"] == "multi"
    r = say(client, sid, "मोबाइल हॉटस्पॉट")
    assert r["profile"]["business_type"] == "Bakery"
    assert r["profile"]["current_internet"] == "Mobile hotspot"


def test_digilocker_and_esign(client):
    o = _order(client)
    oid = o["id"]
    client.post(f"/api/orders/{oid}/consent", json={"accepted": True})
    assert client.post(f"/api/orders/{oid}/digilocker/start", json={"mobile": "98765 43210"}).status_code == 200
    assert client.post(f"/api/orders/{oid}/digilocker/authorise", json={"otp": "000000"}).status_code == 400
    client.post(f"/api/orders/{oid}/digilocker/authorise", json={"otp": "123456"})
    r = client.post(f"/api/orders/{oid}/digilocker/fetch", json={"gstin": "37LDYXK0296F1ZB"}).json()  # K09, active
    assert {f["slot"] for f in r["fetched"]} == {"gst_certificate", "udyam_certificate", "signatory_id", "address_proof"}
    v = client.post(f"/api/orders/{oid}/kyc/verify", json={}).json()
    assert v["verdict"] == "verified", [c for c in v["checks"] if c["status"] != "pass"]
    assert client.post(f"/api/orders/{oid}/esign/request").status_code == 200
    es = client.post(f"/api/orders/{oid}/esign/verify", json={"otp": "123456"}).json()
    assert es["signed"] and len(es["document_hash"]) == 64


def test_digilocker_cancelled_gstin_still_rejected(client):
    oid = _order(client)["id"]
    client.post(f"/api/orders/{oid}/consent", json={"accepted": True})
    client.post(f"/api/orders/{oid}/digilocker/start", json={"mobile": "9876543210"})
    client.post(f"/api/orders/{oid}/digilocker/authorise", json={"otp": "123456"})
    client.post(f"/api/orders/{oid}/digilocker/fetch", json={"gstin": "37IHKXV5167L1ZS"})  # K01, cancelled
    v = client.post(f"/api/orders/{oid}/kyc/verify", json={}).json()
    assert v["verdict"] == "rejected" and any(c["id"] == "gstin.status" for c in v["checks"] if c["status"] == "fail")
    assert client.post(f"/api/orders/{oid}/esign/request").status_code == 409


def test_whatsapp_conversation(client):
    phone = "919811112222"
    wa = lambda text: client.post("/api/whatsapp/simulate", json={"phone": phone, "text": text}).json()["replies"]
    r = wa("hi")
    assert "advisor" in r[0]["text"].lower() and r[0]["list"]
    r = wa("I run a CA firm in Lucknow, 7 staff, 1 office, home broadband, no GST")
    assert any("spend" in m["text"].lower() or "month" in m["text"].lower() for m in r)
    r = wa("3000 rs")
    r = wa("1,2,3")  # pick needs by number
    assert any("₹" in m["text"] and "/month" in m["text"] for m in r)
    btns = next(m for m in r if m.get("buttons"))
    r = wa(btns["buttons"][0]["id"])  # "See price & checkout"
    assert "/quote?session=" in r[0]["text"]


def test_whatsapp_webhook_verify_and_payload(client):
    v = client.get("/api/whatsapp/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "udyam-verify", "hub.challenge": "42"})
    assert v.text == "42"
    payload = {"entry": [{"changes": [{"value": {"messages": [{"from": "919833334444", "type": "text", "text": {"body": "namaste"}}]}}]}]}
    assert client.post("/api/whatsapp/webhook", json=payload).json() == {"ok": True}


def test_impact_simulator(client):
    base = client.post("/api/impact", json={"levers": {k: 0 for k in
                       ["self_serve", "advisor", "instant_quote", "smart_kyc", "fulfilment"]}}).json()
    assert base["scenario"]["activations"] == base["baseline"]["activations"] == 368  # no levers = today
    r = client.post("/api/impact", json={}).json()
    assert r["scenario"]["activations"] > 368 and r["scenario"]["cac"] < r["baseline"]["cac"]
    assert r["scenario"]["days"] < r["baseline"]["days"]
