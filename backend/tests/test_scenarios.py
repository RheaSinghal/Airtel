import pytest

from app.scenarios import SCENARIOS, run_one


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_advisor_scenario(sc):
    r = run_one(sc)
    assert r["passed"], (r["title"], r["failures"], r.get("questions"))
    assert r["turns"] <= 4, f"took {r['turns']} turns: {r['questions']}"


def test_why_not_answers_come_from_rules():
    from app.engine.explain import answer_why
    from app.engine.profile import BusinessProfile

    p = BusinessProfile(segment="prof", city_tier=2, employees=20, sites=1, has_gstin=True)
    assert "Tier-1" in answer_why("why not 1 gbps?", p, {"P02"})
    assert "available" in answer_why("why not leased line?", p, {"P02"})  # ILL 20 is eligible at 20 staff
    p2 = BusinessProfile(segment="micro", city_tier=2, employees=2, sites=1, has_gstin=False)
    assert "GSTIN" in answer_why("why no whatsapp?", p2, {"P01"})
