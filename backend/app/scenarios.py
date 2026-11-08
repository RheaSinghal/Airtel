"""Advisor QA: judge-style scenarios run end to end through the real conversation flow.

Each scenario opens with a free-text message (as an owner would type it), answers any remaining
question from `fill`, picks `needs`, then checks the recommended bundle against expectations and
the rule checker. Run from the back-office ("Advisor QA") or `pytest`.
"""
from __future__ import annotations

from .advisor import flow
from .engine.profile import BusinessProfile
from .engine.rules import check_bundle

SCENARIOS = [
    {"id": "S01", "title": "Kirana, tier-2, no GSTIN", "lang": "en",
     "text": "I have a kirana store in Indore, 2 people, no GST, we use mobile hotspot",
     "needs": ["internet", "payments", "messaging"], "segment": "micro",
     "include": ["P01", "P19"], "exclude": ["P15", "P14", "P03"]},
    {"id": "S02", "title": "Dental clinic, tier-1, GST", "lang": "en",
     "text": "dental clinic in Pune with 8 staff, home broadband, we have GST",
     "needs": ["internet", "email", "backup", "security"], "segment": "prof",
     "include": ["P02", "P16", "P17", "P20"], "exclude": ["P03"]},
    {"id": "S03", "title": "CA firm wants 1 Gbps in a tier-2 city", "lang": "en",
     "text": "CA firm in Lucknow, 20 employees, business broadband, GST registered",
     "needs": ["internet", "email"], "segment": "prof", "exclude": ["P03"]},
    {"id": "S04", "title": "Restaurant chain, 5 outlets", "lang": "en",
     "text": "We run 5 restaurants in Kochi with 60 staff, mixed internet at each site, we have GST",
     "needs": ["internet", "backup_internet", "payments", "cctv", "multi_site_mgmt"], "segment": "multi",
     "include": ["P02", "P09", "P19", "P23", "P10"], "qty": {"P02": 5, "P19": 5}},
    {"id": "S05", "title": "2-store retailer asks for SD-WAN", "lang": "en",
     "text": "apparel shop with 2 stores in Jaipur, 12 staff, business broadband, GST yes",
     "needs": ["internet", "multi_site_mgmt", "payments"], "segment": "micro", "exclude": ["P10"]},
    {"id": "S06", "title": "Textile unit needs a leased line", "lang": "en",
     "text": "textile unit in Surat, 40 workers, 1 factory, leased line from local ISP, GST registered",
     "needs": ["dedicated_line", "iot", "security"], "segment": "mfg",
     "include_any": [["P05", "P06"]], "include": ["P24"]},
    {"id": "S07", "title": "Small workshop (8 staff) wants a leased line", "lang": "en",
     "text": "furniture workshop in Nagpur, 8 workers, 1 unit, GST yes, local ISP",
     "needs": ["dedicated_line", "internet"], "segment": "mfg", "exclude": ["P05", "P06"]},
    {"id": "S08", "title": "Cancelled GSTIN wants WhatsApp", "lang": "en",
     "text": "travel agency in Visakhapatnam, 6 employees, 1 office, mobile hotspot. GSTIN 37IHKXV5167L1ZS",
     "needs": ["internet", "messaging", "telephony"], "segment": "prof", "exclude": ["P15", "P14", "P12"]},
    {"id": "S09", "title": "Salon only wants 2 SIMs", "lang": "en",
     "text": "salon in Patna, 3 people, only want 2 sim cards, no GST, mobile hotspot",
     "segment": "micro", "include": ["P07"], "exclude": ["P01", "P04"], "qty": {"P07": 2}},
    {"id": "S10", "title": "No fibre at the shop", "lang": "en",
     "text": "pharmacy in Bhopal, 3 staff, no fibre available here, no GST, mobile hotspot",
     "needs": ["internet", "payments"], "segment": "micro", "include": ["P04", "P19"], "exclude": ["P01"]},
    {"id": "S11", "title": "Coaching centre wants IVR + toll-free", "lang": "en",
     "text": "coaching centre in Delhi, 12 staff, 1 centre, business broadband, GST registered",
     "needs": ["internet", "telephony", "toll_free"], "segment": "prof", "include": ["P12", "P13"]},
    {"id": "S12", "title": "Pharmacy without GST wants SMS", "lang": "en",
     "text": "chemist shop in Lucknow, 4 people, no GST, home broadband",
     "needs": ["internet", "messaging"], "segment": "micro", "exclude": ["P14", "P15"]},
    {"id": "S13", "title": "Gym chain, 4 sites, guest Wi-Fi + firewall", "lang": "en",
     "text": "gym chain with 4 branches in Bengaluru, 30 employees, business broadband, GST yes",
     "needs": ["internet", "wifi", "security"], "segment": "multi", "include": ["P22"], "qty": {"P22": 4}},
    {"id": "S14", "title": "Hindi: 3 bakeries in Jaipur", "lang": "hi",
     "text": "मेरी जयपुर में 3 बेकरी हैं, 14 लोग काम करते हैं, मोबाइल हॉटस्पॉट, GST है",
     "needs": ["internet", "payments", "cctv"], "segment": "multi", "include": ["P19"], "qty": {"P19": 3}},
    {"id": "S15", "title": "Diagnostic lab: static IP for remote reports", "lang": "en",
     "text": "diagnostic lab in Mumbai, 25 staff, 1 lab, business broadband, GST registered",
     "needs": ["internet", "static_ip", "backup", "security"], "segment": "prof",
     "include": ["P11", "P17"], "include_any": [["P01", "P02", "P03"]]},
    {"id": "S16", "title": "Suspended GSTIN packaging unit", "lang": "en",
     "text": "packaging unit in Pune, 30 workers, 1 factory, leased line, GSTIN 27KYVXC5489I1ZX",
     "needs": ["dedicated_line", "iot", "security"], "segment": "mfg", "exclude": ["P05", "P06", "P24", "P21"]},
]

DEFAULT_FILL = {"current_internet": "Business broadband", "has_gstin": False, "sites": 1, "employees": 5}


def run_one(sc: dict) -> dict:
    s = {"id": f"QA-{sc['id']}", "lang": sc["lang"], "profile": {}, "messages": [], "stage": "collecting",
         "meta": {"expecting": "business_type", "asked": {"business_type": 1}}}
    questions = []
    out = flow.Turn(s).handle(sc["text"], None)
    for _ in range(10):
        if s.get("stage") != "collecting":
            break
        slot = out[-1].get("slot") if out else None
        questions.append(slot)
        if slot == "needs":
            payload = {"set_needs": sc.get("needs", ["internet"])}
        elif slot == "monthly_spend":
            payload = {"skip": "monthly_spend"}
        elif slot in DEFAULT_FILL:
            payload = {"set": {slot: sc.get("fill", {}).get(slot, DEFAULT_FILL[slot])}}
        else:
            return {**_head(sc), "passed": False, "failures": [f"stuck on unexpected question: {slot}"], "questions": questions}
        out = flow.Turn(s).handle(None, payload)

    rec = s.get("recommendation") or {}
    failures = []
    if not rec.get("default"):
        return {**_head(sc), "passed": False, "failures": ["no recommendation"], "questions": questions}
    tier = rec["tiers"][rec["default"]]
    ids = {l["product_id"]: l["quantity"] for l in tier["lines"]}
    p = BusinessProfile(**{k: v for k, v in s["profile"].items() if k in BusinessProfile.model_fields})

    if sc.get("segment") and p.segment != sc["segment"]:
        failures.append(f"segment {p.segment}, expected {sc['segment']}")
    for pid in sc.get("include", []):
        if pid not in ids:
            failures.append(f"missing {pid}")
    for group in sc.get("include_any", []):
        if not set(group) & ids.keys():
            failures.append(f"needs one of {group}")
    for pid in sc.get("exclude", []):
        if pid in ids:
            failures.append(f"should not include {pid}")
    for pid, q in sc.get("qty", {}).items():
        if ids.get(pid) != q:
            failures.append(f"{pid} quantity {ids.get(pid)}, expected {q}")
    for name, t in rec["tiers"].items():  # every tier must be sellable
        problems = check_bundle([(l["product_id"], l["quantity"]) for l in t["lines"]], p)
        if problems:
            failures.append(f"{name} tier breaks rules: {problems}")
    return {
        **_head(sc), "passed": not failures, "failures": failures, "questions": questions,
        "turns": len(questions) + 1, "segment": p.segment,
        "bundle": [{"product_id": l["product_id"], "name": l["name"], "qty": l["quantity"]} for l in tier["lines"]],
        "monthly_total": tier["totals"]["monthly_total"],
        "excluded": [f"{w['name']}: {'; '.join(w['reasons'])}" for w in rec.get("why_not", [])
                     if w["product_id"] in sc.get("exclude", [])],
    }


def _head(sc: dict) -> dict:
    return {"id": sc["id"], "title": sc["title"], "input": sc["text"], "lang": sc["lang"]}


def run_all() -> dict:
    results = [run_one(sc) for sc in SCENARIOS]
    passed = sum(r["passed"] for r in results)
    turns = [r.get("turns", 0) for r in results if r.get("turns")]
    return {"passed": passed, "total": len(results), "avg_turns": round(sum(turns) / len(turns), 1) if turns else None,
            "results": results}
