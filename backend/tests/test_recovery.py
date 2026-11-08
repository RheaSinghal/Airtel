"""N3 recovery playbook and D4 leads audit."""
from app import backoffice, recovery
from app.engine.offer import build_offer
from app.engine.profile import BusinessProfile

CLINIC = BusinessProfile(business_type="Dental clinic", segment="prof", city="Pune", city_tier=1, employees=8, sites=1,
                         has_gstin=True, monthly_spend=4000, needs=["internet", "email", "backup"])


def test_every_drop_reason_maps_to_a_family():
    import pandas as pd
    from app.data import leads
    for reason in leads().drop_reason.dropna().unique():
        assert any(reason in r for r in recovery.FAMILY.values()), reason


def test_price_drop_gets_engine_priced_36_month_offer():
    pb = recovery.playbook(CLINIC, "Price too high", "Marathi")
    assert pb["family"] == "price" and pb["offer"]["contract_months"] == 36
    t36 = build_offer(CLINIC, "en", 36)["tiers"]
    assert pb["offer"]["monthly_total"] in {t["totals"]["monthly_total"] for t in t36.values() if t}
    assert pb["offer"]["monthly_total"] <= build_offer(CLINIC, "en", 12)["tiers"]["recommended"]["totals"]["monthly_total"]
    assert "Marathi" in pb["brief"][0]


def test_reason_specific_actions():
    assert "DigiLocker" in recovery.playbook(CLINIC, "Missing GST or Udyam document")["action"]
    assert "AirFiber" in recovery.playbook(CLINIC, "Site not feasible for fibre")["action"]
    mob = recovery.playbook(CLINIC, "Only wanted a mobile plan")
    assert all("Postpaid" in p for p in mob["offer"]["products"])
    q = recovery.playbook(CLINIC, "Quote too complex to understand", "Hindi")
    assert len(q["brief"]) == 4 and "नमस्ते" in q["brief"][0]


def test_call_list_has_recovery_for_every_row():
    rows = backoffice.historical_call_list(30)
    assert rows and all(r["recovery"] and r["recovery"]["action"] for r in rows)


def test_leads_audit_finds_planted_violations():
    a = backoffice.audit()
    by = {c["check"]: c for c in a["checks"]}
    assert by["inactive_gstin"]["distinct_leads"] == 22
    assert by["gstin_product_without_gstin"]["distinct_leads"] == 11
    assert by["city_tier"]["distinct_leads"] == 24
    assert by["min_employees"]["distinct_leads"] == 8
    assert by["missing_dependency"]["distinct_leads"] == 9
    assert a["flagged_activations"] == 68 and a["activations"] == 368
