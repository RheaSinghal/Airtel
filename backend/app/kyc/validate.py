"""Cross-document KYC validation.

Each check returns pass / warn / fail with a plain-language message. The verdict:
  verified         - no fails, no warns
  needs_attention  - warns only (a human or the customer can resolve it, order may proceed)
  rejected         - at least one fail (customer must fix / re-upload before activation)
"""
from __future__ import annotations

import re
from datetime import date
from difflib import SequenceMatcher

from ..config import ADDRESS_PROOF_MAX_AGE_DAYS, TODAY
from ..data import gstin_registry, udyam_registry
from .identifiers import mask_gstin, mask_udyam, validate_gstin, validate_udyam
from .parse import pincode

REQUIRED_DOCS = ("gst_certificate", "signatory_id", "address_proof", "udyam_certificate")

MSG = {
    "en": {
        "doc_missing": "{doc} has not been uploaded yet.",
        "doc_unreadable": "{doc} is too blurry to read. Please retake the photo in good light.",
        "doc_wrong_type": "This looks like a {found}, not a {doc}. Please upload the right document.",
        "gstin_missing": "We could not find a GSTIN on the GST certificate.",
        "gstin_format": "GSTIN {gstin} is not in a valid format.",
        "gstin_checksum": "GSTIN {gstin} fails the check-digit test, so it may have a typo or have been altered.",
        "gstin_ok": "GSTIN {gstin} is valid.",
        "gstin_not_found": "GSTIN {gstin} is not in the GST registry.",
        "gstin_status": "GSTIN {gstin} is {status} in the GST registry, so GST-based services cannot be activated.",
        "gstin_active": "GSTIN {gstin} is active in the GST registry.",
        "gst_name_mismatch": "The name on the GST certificate (\"{doc}\") does not match the GST registry (\"{reg}\").",
        "gst_name_ok": "The business name matches the GST registry.",
        "gst_address_mismatch": "The address on the GST certificate does not match the GST registry.",
        "udyam_missing_number": "The Udyam certificate has no readable Udyam number.",
        "udyam_format": "Udyam number {udyam} is not in a valid format.",
        "udyam_not_found": "Udyam number {udyam} is not in the Udyam registry.",
        "udyam_ok": "Udyam {udyam} found in the Udyam registry.",
        "udyam_name_mismatch": "The Udyam enterprise name (\"{doc}\") does not match the GST trade name (\"{gst}\").",
        "udyam_state_mismatch": "The Udyam state ({udyam_state}) does not match the GSTIN state ({gst_state}).",
        "addr_old": "The address proof is dated {bill_date}, which is {age} days old. It must be under {max} days old.",
        "addr_future": "The address proof date {bill_date} is in the future.",
        "addr_ok": "The address proof is recent ({age} days old).",
        "addr_name_mismatch": "The address proof is billed to \"{doc}\", not the business \"{gst}\".",
        "addr_pin_mismatch": "The PIN code on the address proof ({doc}) does not match the GST address ({gst}).",
        "id_expired": "The signatory ID expired on {valid_till}.",
        "id_business_mismatch": "The signatory ID is for \"{doc}\", not \"{gst}\".",
        "prop_signatory": "For a proprietorship the signatory should be the proprietor ({prop}), but the ID is for {name}.",
        "auth_letter": "For {constitution} we will need an authorisation letter for {name} ({designation}) at installation.",
    },
    "hi": {
        "doc_missing": "{doc} अभी अपलोड नहीं हुआ है।",
        "doc_unreadable": "{doc} धुंधला है और पढ़ा नहीं जा रहा। कृपया अच्छी रोशनी में दोबारा फ़ोटो लें।",
        "doc_wrong_type": "यह {doc} नहीं बल्कि {found} लग रहा है। कृपया सही डॉक्यूमेंट अपलोड करें।",
        "gstin_missing": "GST सर्टिफ़िकेट पर GSTIN नहीं मिला।",
        "gstin_format": "GSTIN {gstin} का फ़ॉर्मेट सही नहीं है।",
        "gstin_checksum": "GSTIN {gstin} चेक-डिजिट टेस्ट में फ़ेल है। हो सकता है इसमें टाइपो हो या इसे बदला गया हो।",
        "gstin_ok": "GSTIN {gstin} वैध है।",
        "gstin_not_found": "GSTIN {gstin} GST रजिस्ट्री में नहीं है।",
        "gstin_status": "GST रजिस्ट्री में GSTIN {gstin} {status} है, इसलिए GST वाली सेवाएँ चालू नहीं की जा सकतीं।",
        "gstin_active": "GST रजिस्ट्री में GSTIN {gstin} एक्टिव है।",
        "gst_name_mismatch": "GST सर्टिफ़िकेट पर नाम (\"{doc}\") GST रजिस्ट्री (\"{reg}\") से मेल नहीं खाता।",
        "gst_name_ok": "बिज़नेस का नाम GST रजिस्ट्री से मेल खाता है।",
        "gst_address_mismatch": "GST सर्टिफ़िकेट का पता GST रजिस्ट्री से मेल नहीं खाता।",
        "udyam_missing_number": "Udyam सर्टिफ़िकेट पर Udyam नंबर पढ़ा नहीं जा रहा।",
        "udyam_format": "Udyam नंबर {udyam} का फ़ॉर्मेट सही नहीं है।",
        "udyam_not_found": "Udyam नंबर {udyam} Udyam रजिस्ट्री में नहीं है।",
        "udyam_ok": "Udyam {udyam} रजिस्ट्री में मिल गया।",
        "udyam_name_mismatch": "Udyam पर एंटरप्राइज़ का नाम (\"{doc}\") GST ट्रेड नाम (\"{gst}\") से मेल नहीं खाता।",
        "udyam_state_mismatch": "Udyam का राज्य ({udyam_state}) GSTIN के राज्य ({gst_state}) से मेल नहीं खाता।",
        "addr_old": "पते का प्रमाण {bill_date} का है, यानी {age} दिन पुराना। यह {max} दिन से कम पुराना होना चाहिए।",
        "addr_future": "पते के प्रमाण की तारीख {bill_date} भविष्य की है।",
        "addr_ok": "पते का प्रमाण हाल का है ({age} दिन पुराना)।",
        "addr_name_mismatch": "पते का प्रमाण \"{doc}\" के नाम पर है, बिज़नेस \"{gst}\" के नाम पर नहीं।",
        "addr_pin_mismatch": "पते के प्रमाण का पिन कोड ({doc}) GST पते के पिन कोड ({gst}) से मेल नहीं खाता।",
        "id_expired": "साइनेटरी ID की वैधता {valid_till} को ख़त्म हो चुकी है।",
        "id_business_mismatch": "साइनेटरी ID \"{doc}\" के लिए है, \"{gst}\" के लिए नहीं।",
        "prop_signatory": "प्रोप्राइटरशिप में साइनेटरी प्रोप्राइटर ({prop}) होना चाहिए, लेकिन ID {name} की है।",
        "auth_letter": "{constitution} के लिए इंस्टॉलेशन के समय {name} ({designation}) का ऑथराइज़ेशन लेटर चाहिए होगा।",
    },
}

DOC_NAMES = {
    "en": {"gst_certificate": "GST certificate", "udyam_certificate": "Udyam certificate",
           "signatory_id": "Signatory ID", "address_proof": "Address proof"},
    "hi": {"gst_certificate": "GST सर्टिफ़िकेट", "udyam_certificate": "Udyam सर्टिफ़िकेट",
           "signatory_id": "साइनेटरी ID", "address_proof": "पते का प्रमाण"},
}


def _norm(s: str | None) -> str:
    """Lowercase, drop punctuation and spaces (OCR often merges words)."""
    s = (s or "").lower().replace("&", "and")
    s = re.sub(r"\b(pvt|private|ltd|limited|llp)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def similar(a: str | None, b: str | None, threshold: float = 0.88) -> bool:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return False
    return na == nb or SequenceMatcher(None, na, nb).ratio() >= threshold


def same_legal_name(a: str | None, b: str | None) -> bool:
    """'Person (Prop. Business)' names are compared part by part, so a swapped business name
    cannot hide behind a long shared prefix."""
    pa, pb = _split_legal(a), _split_legal(b)
    if pa and pb:
        return similar(pa[0], pb[0]) and similar(pa[1], pb[1])
    return similar(a, b, threshold=0.92)


def _split_legal(name: str | None):
    m = re.match(r"\s*(.+?)\s*\(\s*Prop\.?\s*(.+?)\)\s*$", name or "")
    return (m.group(1), m.group(2)) if m else None


def proprietor_name(legal_name: str | None) -> str | None:
    m = re.match(r"\s*(.+?)\s*\(\s*Prop\.", legal_name or "")
    return m.group(1) if m else None


def _days_old(d: str) -> int | None:
    try:
        return (TODAY - date.fromisoformat(d)).days
    except (TypeError, ValueError):
        return None


class _Report:
    def __init__(self, lang: str):
        self.lang = lang if lang in MSG else "en"
        self.checks: list[dict] = []

    def add(self, _id: str, _level: str, _msg: str, _doc: str | None = None, /, **kw):
        text = MSG[self.lang][_msg].format(**kw)
        self.checks.append({"id": _id, "status": _level, "code": _msg, "doc": _doc, "message": text})

    def doc_name(self, d: str) -> str:
        return DOC_NAMES[self.lang][d]


def verify(docs: dict[str, dict], lang: str = "en", has_udyam: bool | None = None) -> dict:
    """`docs` maps doc_type -> {"fields": {...}, "quality": {...}, "detected_type": str|None}."""
    r = _Report(lang)
    usable: dict[str, dict] = {}

    # 1. Presence and quality
    for d in REQUIRED_DOCS:
        doc = docs.get(d)
        if not doc:
            if d == "udyam_certificate" and has_udyam is False:
                continue  # Udyam is optional for businesses that are not registered
            r.add(f"{d}.present", "fail", "doc_missing", d, doc=r.doc_name(d))
            continue
        q = doc.get("quality", {})
        if q.get("unreadable"):
            r.add(f"{d}.quality", "fail", "doc_unreadable", d, doc=r.doc_name(d))
            continue
        found = doc.get("detected_type")
        if found and found != d:
            r.add(f"{d}.type", "fail", "doc_wrong_type", d, doc=r.doc_name(d), found=r.doc_name(found))
            continue
        usable[d] = doc.get("fields", {})

    gst = usable.get("gst_certificate")
    reg = None
    gstin = None

    # 2. GSTIN: structure, checksum, registry status, name and address
    if gst is not None:
        if not gst.get("gstin"):
            r.add("gstin.present", "fail", "gstin_missing", "gst_certificate")
        else:
            v = validate_gstin(gst["gstin"])
            gstin = v["gstin"]
            masked = mask_gstin(gstin)
            if not v["format_ok"]:
                r.add("gstin.format", "fail", "gstin_format", "gst_certificate", gstin=masked)
            elif not v["checksum_ok"]:
                r.add("gstin.checksum", "fail", "gstin_checksum", "gst_certificate", gstin=masked)
            else:
                r.add("gstin.checksum", "pass", "gstin_ok", "gst_certificate", gstin=masked)
                reg = gstin_registry().get(gstin)
                if reg is None:
                    r.add("gstin.registry", "fail", "gstin_not_found", "gst_certificate", gstin=masked)
                elif reg["status"] != "Active":
                    r.add("gstin.status", "fail", "gstin_status", "gst_certificate", gstin=masked, status=reg["status"])
                else:
                    r.add("gstin.status", "pass", "gstin_active", "gst_certificate", gstin=masked)
                if reg is not None:
                    name_ok = same_legal_name(gst.get("legal_name"), reg["legal_name"]) and similar(
                        gst.get("trade_name") or reg["trade_name"], reg["trade_name"])
                    if name_ok:
                        r.add("gst.name", "pass", "gst_name_ok", "gst_certificate")
                    else:
                        r.add("gst.name", "fail", "gst_name_mismatch", "gst_certificate",
                              doc=gst.get("legal_name", ""), reg=reg["legal_name"])
                    if pincode(gst.get("address")) and pincode(gst.get("address")) != pincode(reg["principal_place_of_business"]):
                        r.add("gst.address", "fail", "gst_address_mismatch", "gst_certificate")

    business = (reg or {}).get("trade_name") or (gst or {}).get("trade_name")
    legal = (reg or {}).get("legal_name") or (gst or {}).get("legal_name")
    constitution = (reg or {}).get("constitution") or (gst or {}).get("constitution")
    gst_state = (reg or {}).get("state")
    gst_pin = pincode((reg or {}).get("principal_place_of_business") or (gst or {}).get("address"))

    # 3. Udyam
    ud = usable.get("udyam_certificate")
    if ud is not None:
        if not ud.get("udyam_number"):
            r.add("udyam.number", "fail", "udyam_missing_number", "udyam_certificate")
        else:
            v = validate_udyam(ud["udyam_number"])
            masked = mask_udyam(v["udyam_number"])
            if not v["format_ok"]:
                r.add("udyam.format", "fail", "udyam_format", "udyam_certificate", udyam=masked)
            else:
                ureg = udyam_registry().get(v["udyam_number"])
                if ureg is None:
                    r.add("udyam.registry", "fail", "udyam_not_found", "udyam_certificate", udyam=masked)
                else:
                    r.add("udyam.registry", "pass", "udyam_ok", "udyam_certificate", udyam=masked)
                    if business and not (similar(ureg["enterprise_name"], business) or similar(ureg["enterprise_name"], legal)):
                        r.add("udyam.name", "fail", "udyam_name_mismatch", "udyam_certificate",
                              doc=ureg["enterprise_name"], gst=business)
                    if not similar(ud.get("enterprise_name"), ureg["enterprise_name"]):
                        r.add("udyam.doc_name", "fail", "udyam_name_mismatch", "udyam_certificate",
                              doc=ud.get("enterprise_name", ""), gst=ureg["enterprise_name"])
                    if gst_state and ureg["state"] != gst_state:
                        r.add("udyam.state", "warn", "udyam_state_mismatch", "udyam_certificate",
                              udyam_state=ureg["state"], gst_state=gst_state)

    # 4. Address proof: recency, name, PIN
    ap = usable.get("address_proof")
    if ap is not None:
        age = _days_old(ap.get("bill_date"))
        if age is None:
            r.add("address.date", "warn", "addr_old", "address_proof", bill_date="?", age="?", max=ADDRESS_PROOF_MAX_AGE_DAYS)
        elif age < 0:
            r.add("address.date", "fail", "addr_future", "address_proof", bill_date=ap["bill_date"])
        elif age > ADDRESS_PROOF_MAX_AGE_DAYS:
            r.add("address.date", "fail", "addr_old", "address_proof", bill_date=ap["bill_date"], age=age, max=ADDRESS_PROOF_MAX_AGE_DAYS)
        else:
            r.add("address.date", "pass", "addr_ok", "address_proof", age=age)
        if business and not (similar(ap.get("billed_to"), business) or similar(ap.get("billed_to"), legal)):
            r.add("address.name", "warn", "addr_name_mismatch", "address_proof", doc=ap.get("billed_to", ""), gst=business)
        ap_pin = pincode(ap.get("address"))
        if gst_pin and ap_pin and ap_pin != gst_pin:
            r.add("address.pin", "fail", "addr_pin_mismatch", "address_proof", doc=ap_pin, gst=gst_pin)

    # 5. Signatory
    sid = usable.get("signatory_id")
    if sid is not None:
        days_left = _days_old(sid.get("valid_till"))
        if days_left is not None and days_left > 0:
            r.add("signatory.validity", "fail", "id_expired", "signatory_id", valid_till=sid["valid_till"])
        if business and sid.get("business_name") and not (similar(sid["business_name"], business) or similar(sid["business_name"], legal)):
            r.add("signatory.business", "fail", "id_business_mismatch", "signatory_id", doc=sid["business_name"], gst=business)
        prop = proprietor_name(legal)
        if constitution == "Proprietorship" and prop and sid.get("name") and not similar(sid["name"], prop):
            r.add("signatory.proprietor", "fail", "prop_signatory", "signatory_id", prop=prop, name=sid["name"])
        elif constitution and constitution != "Proprietorship" and sid.get("name"):
            r.add("signatory.authority", "info", "auth_letter", "signatory_id", constitution=constitution,
                  name=sid["name"], designation=sid.get("designation", ""))

    statuses = {c["status"] for c in r.checks}
    verdict = "rejected" if "fail" in statuses else "needs_attention" if "warn" in statuses else "verified"
    gst_ok = reg is not None and reg["status"] == "Active" and not any(
        c["status"] == "fail" and c["id"].startswith(("gstin", "gst.")) for c in r.checks)
    return {
        "verdict": verdict,
        "gst_verified": gst_ok,
        "gstin_status": (reg or {}).get("status"),
        "business_name": business,
        "constitution": constitution,
        "checks": r.checks,
    }
