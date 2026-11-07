import pandas as pd
import pytest

from app.data import SEGMENT_CODES, catalogue, leads
from app.engine.bundler import recommend
from app.engine.pricing import quote, unit_price
from app.engine.profile import BusinessProfile
from app.engine.rules import check_bundle

ALL_NEEDS = ["payments", "messaging", "email", "backup", "security", "cctv", "wifi", "website",
             "telephony", "toll_free", "static_ip", "multi_site_mgmt", "iot", "fleet", "backup_internet", "mobile_lines"]


def ids(tier):
    return {i["product_id"] for i in tier["items"]}


def test_tier1_only_product_never_offered_in_tier2():
    p = BusinessProfile(segment="prof", city_tier=2, employees=40, sites=1, has_gstin=True, needs=["email"])
    for tier in recommend(p)["tiers"].values():
        assert "P03" not in ids(tier)


def test_no_gstin_blocks_gst_products():
    p = BusinessProfile(segment="micro", city_tier=1, employees=3, sites=1, has_gstin=False,
                        needs=["messaging", "payments", "telephony"])
    gst_products = {pid for pid, prod in catalogue().items() if prod.requires_gstin}
    rec = recommend(p)
    for tier in rec["tiers"].values():
        assert not ids(tier) & gst_products
    notes = rec["tiers"]["recommended"]["notes"]
    assert any(n["code"] == "excluded" and n["product_id"] == "P15" for n in notes)


def test_cancelled_gstin_treated_as_no_gstin():
    p = BusinessProfile(segment="mfg", city_tier=2, employees=30, sites=1, has_gstin=True,
                        gstin_status="Cancelled", needs=["dedicated_line", "iot"])
    rec = recommend(p)["tiers"]["recommended"]
    assert not ids(rec) & {"P05", "P06", "P24"}
    assert any(b.get("code") == "gstin_inactive" for n in rec["notes"] for b in n.get("blocks", []))


def test_sdwan_needs_three_sites():
    p = BusinessProfile(segment="multi", city_tier=1, employees=40, sites=2, has_gstin=True, needs=["multi_site_mgmt"])
    assert "P10" not in ids(recommend(p)["tiers"]["recommended"])


def test_dependency_pulls_in_connectivity():
    p = BusinessProfile(segment="micro", city_tier=2, employees=2, sites=1, has_gstin=False, only_mobile=True,
                        needs=["cctv"], mobile_lines=1)
    rec = ids(recommend(p)["tiers"]["recommended"])
    assert "P23" in rec and rec & {"P01", "P04"}


def test_only_mobile_gets_only_lines():
    p = BusinessProfile(segment="micro", city_tier=2, employees=3, sites=1, has_gstin=False, only_mobile=True, mobile_lines=2)
    rec = recommend(p)
    assert list(rec["tiers"]) == ["recommended"]
    assert ids(rec["tiers"]["recommended"]) == {"P07"}


def test_no_fibre_uses_airfiber():
    p = BusinessProfile(segment="micro", city_tier=2, employees=2, sites=1, has_gstin=False, fibre_available=False, needs=["payments"])
    assert "P04" in ids(recommend(p)["tiers"]["recommended"])


def test_pricing_commit_longer_pay_less():
    prod = catalogue()["P01"]  # 999-1199, min 12 months
    assert unit_price(prod, 12) == 1199
    assert unit_price(prod, 24) == 1099
    assert unit_price(prod, 36) == 999
    assert unit_price(catalogue()["P06"], 12) == 35000  # min 24 -> forced to 24 -> top of range


def test_quote_totals_include_gst():
    q = quote([{"product_id": "P01", "quantity": 1}, {"product_id": "P07", "quantity": 2}], 12)
    t = q["totals"]
    assert t["monthly_before_tax"] == 1199 + 2 * unit_price(catalogue()["P07"], 12)
    assert t["monthly_total"] == t["monthly_before_tax"] + t["monthly_gst"]


def _profile_from_lead(r) -> BusinessProfile:
    return BusinessProfile(
        segment=SEGMENT_CODES[r.segment], city=r.city, city_tier=int(r.city_tier),
        employees=int(r.employee_count), sites=int(r.num_sites), has_gstin=r.has_gstin == "Y",
        needs=ALL_NEEDS,
    )


@pytest.mark.parametrize("seg", list(SEGMENT_CODES))
def test_every_lead_profile_gets_a_fully_eligible_bundle(seg):
    """Property test over the real leads: every tier we generate must pass the rule checker."""
    df = leads()
    df = df[df.segment == seg].drop_duplicates(["city_tier", "employee_count", "num_sites", "has_gstin"])
    for r in df.itertuples(index=False):
        p = _profile_from_lead(r)
        for name, tier in recommend(p)["tiers"].items():
            items = [(i["product_id"], i["quantity"]) for i in tier["items"]]
            assert check_bundle(items, p) == [], (r.lead_id, name, items)
