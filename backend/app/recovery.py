"""N3 Recovery playbook: what a field rep or partner should offer and say for each lost lead.

Routing (backoffice.suggested_owner) says *who* calls. This says *what to offer*, and the offer is
still priced by the rules engine, so a rep can never promise a price the engine wouldn't give.
"""
from __future__ import annotations

from .engine.offer import build_offer
from .engine.profile import BusinessProfile

# Product of interest -> advisor need, to rebuild a profile from a historical lead row.
NEED_OF = {"P01": "internet", "P02": "internet", "P03": "internet", "P04": "internet", "P05": "dedicated_line",
           "P06": "dedicated_line", "P07": "mobile_lines", "P08": "mobile_lines", "P09": "backup_internet",
           "P10": "multi_site_mgmt", "P11": "static_ip", "P12": "telephony", "P13": "toll_free", "P14": "messaging",
           "P15": "messaging", "P16": "email", "P17": "backup", "P18": "website", "P19": "payments",
           "P20": "security", "P21": "security", "P22": "wifi", "P23": "cctv", "P24": "iot", "P25": "fleet"}

FAMILY = {
    "price": {"Price too high", "Competitor offered cheaper plan", "saw_offer_did_not_buy"},
    "locked_in": {"Locked in with current provider"},
    "quote": {"Quote too complex to understand", "Quote took too long to arrive"},
    "contact": {"Unreachable after 3 attempts", "Owner had no time for a visit", "Visit not scheduled by sales",
                "Wrong or invalid number", "Not interested on first call", "Decided to wait", "abandoned_mid_chat"},
    "kyc": {"Missing GST or Udyam document", "Found paperwork too long", "Document details did not match",
            "Authorised signatory not available", "kyc_failed"},
    "install": {"Site not feasible for fibre", "Installation delayed beyond 21 days", "Customer cancelled before install"},
    "mobile_only": {"Only wanted a mobile plan"},
    "payment": {"First payment failed"},
    "human": {"asked_for_human", "wants_expert"},
}

LANG_CODE = {"Hindi": "hi", "English": "en", "Marathi": "mr", "Tamil": "ta", "Telugu": "te", "Kannada": "kn",
             "Bengali": "bn", "Gujarati": "gu", "Malayalam": "ml", "Punjabi": "pa"}
OPENER = {
    "en": "Hello, this is Accel Business. You'd looked at internet for your business, and I have a simpler offer.",
    "hi": "नमस्ते, मैं Accel Business से बोल रहा/रही हूँ। आपने अपने बिज़नेस के लिए इंटरनेट देखा था, आपके लिए एक आसान ऑफ़र है।",
}


def family(reason: str | None) -> str:
    return next((f for f, reasons in FAMILY.items() if reason in reasons), "contact")


def profile_from_lead(r) -> BusinessProfile:
    from .data import SEGMENT_CODES
    needs = sorted({NEED_OF[p] for p in str(r.products_of_interest or "").split(";") if p in NEED_OF}) or ["internet"]
    return BusinessProfile(
        business_type=r.business_type, segment=SEGMENT_CODES.get(r.segment), city=r.city, city_tier=int(r.city_tier),
        employees=int(r.employee_count), sites=int(r.num_sites), has_gstin=r.has_gstin == "Y",
        monthly_spend=int(r.monthly_telecom_spend_inr or 0) or None, needs=needs)


def _tier(offer: dict, name: str | None = None) -> dict | None:
    return offer["tiers"].get(name or offer["default"] or "")


def _brief_offer(t: dict, months: int) -> dict:
    return {"tier": t["label"], "monthly_total": t["totals"]["monthly_total"], "contract_months": months,
            "ready_in_days": t["totals"]["ready_in_days"], "products": [l["name"] for l in t["lines"]]}


def playbook(p: BusinessProfile, reason: str | None, language: str = "Hindi", partner_id: str | None = None) -> dict:
    fam = family(reason)
    lang = LANG_CODE.get(language, "en")
    base = build_offer(p, "en", 12)
    t12 = _tier(base)
    if not t12:
        return {"family": fam, "action": "Field visit: no self-serve bundle fits this profile.", "offer": None,
                "brief": [], "language": language}
    offer, action, say = _brief_offer(t12, 12), "", []
    if fam in ("price", "locked_in"):
        long = build_offer(p, "en", 36)
        same = _tier(long)  # the same tier, just committed longer
        pick, note = same, ""
        if p.monthly_spend and same["totals"]["monthly_before_tax"] > p.monthly_spend:
            fits = [n for n in ("recommended", "essential") if _tier(long, n)
                    and _tier(long, n)["totals"]["monthly_before_tax"] <= p.monthly_spend]
            if fits:
                pick, note = _tier(long, fits[0]), f" The {_tier(long, fits[0])['label']} tier fits today's ₹{p.monthly_spend:,} spend."
        offer = _brief_offer(pick, 36)
        saving = t12["totals"]["monthly_total"] - same["totals"]["monthly_total"]
        action = "Re-quote on a 36-month contract" + (" within today's spend" if note else "")
        say.append(f"Same bundle on 36 months: ₹{same['totals']['monthly_total']:,}/month including GST"
                   + (f", ₹{saving:,} less than the 12-month quote." if saving > 0 else ".") + note)
        if fam == "locked_in":
            say.append("Book now, activate when the current lock-in ends; the price is held.")
    elif fam == "quote":
        action = "Send a 3-line WhatsApp quote"
        say += [f"1. {offer['tier']}: {', '.join(offer['products'])}.",
                f"2. ₹{offer['monthly_total']:,} per month, GST included. Nothing else to pay monthly.",
                f"3. Ready in about {offer['ready_in_days']} days after KYC."]
    elif fam == "kyc":
        action = "Send DigiLocker link + remote Aadhaar e-Sign"
        say.append("No photos needed: DigiLocker shares your GST and Udyam records in about 30 seconds; "
                   "the signatory can e-sign from their own phone.")
    elif fam == "install":
        p2 = p.model_copy(update={"fibre_available": False})
        t = _tier(build_offer(p2, "en", 12))
        if t:
            offer = _brief_offer(t, 12)
        action = "Re-plan on 5G AirFiber"
        say.append(f"Fastest feasible plan with 5G AirFiber: ready in about {offer['ready_in_days']} days, "
                   f"₹{offer['monthly_total']:,}/month including GST.")
    elif fam == "mobile_only":
        p2 = p.model_copy(update={"only_mobile": True, "needs": ["mobile_lines"]})
        t = _tier(build_offer(p2, "en", 12))
        if t:
            offer = _brief_offer(t, 12)
        action = "Offer business SIMs only, upsell later"
        say.append(f"Just the business SIMs: ₹{offer['monthly_total']:,}/month, on one GST bill.")
    elif fam == "payment":
        action = "Send UPI AutoPay retry link"
        say.append("Your order is saved; pay the first bill by UPI and set AutoPay so it never fails again.")
    elif fam == "human":
        action = "Field visit with this brief"
        say.append(f"Recommended starting point: {offer['tier']} at ₹{offer['monthly_total']:,}/month.")
    else:  # contact friction: don't chase for a visit, hand them the self-serve journey
        action = "Send self-serve advisor link on WhatsApp" + (" (partner keeps credit)" if partner_id else "")
        say.append(f"Takes 3 minutes on your phone, in {language}. Starting at ₹{offer['monthly_total']:,}/month.")
    return {"family": fam, "action": action, "offer": offer, "language": language,
            "brief": [OPENER.get(lang, OPENER["en"] + f" (Speak in {language}.)")] + say,
            "link": f"/advisor?partner={partner_id}" if partner_id else "/advisor"}
