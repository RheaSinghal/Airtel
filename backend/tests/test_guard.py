"""N1 fact guard: LLM text is used only when every number and product traces to engine facts."""
from app import guard
from app.advisor import flow

FACTS = {"monthly_total_incl_gst": 2914, "items": [{"product": "Biz Fibre 100", "qty": 1, "monthly": 799}],
         "left_out": []}


def test_traceable_text_passes():
    assert guard.check("Your plan is ₹2,914 a month. Biz Fibre 100 costs ₹799.", FACTS) == []


def test_invented_price_is_blocked():
    problems = guard.check("Only ₹2,499 per month!", FACTS)
    assert any("2499" in p for p in problems)


def test_indic_digits_are_checked():
    assert guard.check("कुल ₹२,९१४ प्रति माह", FACTS) == []
    assert guard.check("कुल ₹२,४९९ प्रति माह", FACTS)


def test_small_counts_are_free():
    assert guard.check("Ready in 3 days for your 12 staff, 24 month contract.", FACTS) == []


def test_unlisted_product_and_promo_blocked():
    assert guard.check("We also add Managed Firewall.", FACTS)
    assert guard.check("You get a 10% discount.", FACTS)
    assert guard.check("Toll-free calls are included.", {"items": ["Toll-Free Number"]}) == []


def test_vet_falls_back_and_counts():
    before = guard.stats()["blocked"]
    assert guard.vet("Just ₹1,999!", FACTS, "TEMPLATE") == "TEMPLATE"
    assert guard.vet("₹2,914 per month", FACTS, "TEMPLATE") == "₹2,914 per month"
    assert guard.vet(None, FACTS, "TEMPLATE") == "TEMPLATE"
    assert guard.stats()["blocked"] == before + 1


def test_advisor_never_shows_hallucinated_price(monkeypatch):
    """Even if the LLM invents a price, the owner sees the engine template."""
    monkeypatch.setattr(flow.llm, "enabled", lambda: True)
    monkeypatch.setattr(flow.llm, "extract_profile", lambda *a, **k: None)
    monkeypatch.setattr(flow.llm, "phrase", lambda text, lang, **k: text)
    monkeypatch.setattr(flow.llm, "explain", lambda facts, lang: "Special offer: only ₹1 per month, plus a free laptop!")
    monkeypatch.setattr(flow, "_llm_facts", lambda *a, **k: {}, raising=False)
    from app.main import app
    from fastapi.testclient import TestClient
    c = TestClient(app)
    sid = c.post("/api/advisor/sessions", json={"lang": "en"}).json()["id"]

    def say(text=None, payload=None):
        return c.post(f"/api/advisor/sessions/{sid}/messages", json={"text": text, "payload": payload}).json()

    say("I run a dental clinic in Pune with 8 staff, we use home broadband and pay about Rs 4000 a month")
    say(payload={"set": {"sites": 1}})
    say(payload={"set": {"has_gstin": False}})
    r = say(payload={"set_needs": ["internet", "email", "backup"]})
    rec = next(m for m in r["messages"] if m.get("kind") == "recommendation")
    assert "free laptop" not in rec["explanation"] and "₹1 per" not in rec["explanation"]
    assert "•" in rec["explanation"]  # the engine template was used instead
