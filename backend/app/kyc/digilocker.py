"""Mock DigiLocker pull and Aadhaar e-Sign.

Issuer-signed documents (GSTN, MSME/Udyam, UIDAI e-KYC) arrive as structured data, so there is
nothing to OCR and nothing to forge. In production these calls go to the DigiLocker Partner API
and a licensed e-Sign ASP; here they read the mock registries. The demo OTP is 123456.
"""
from __future__ import annotations

import hashlib
import json
import secrets

from .. import store
from ..config import TODAY
from ..data import gstin_registry, udyam_registry
from .identifiers import mask_gstin, validate_gstin
from .validate import proprietor_name, similar

DEMO_OTP = "123456"


class DigiLockerError(ValueError):
    pass


def _extras(order_id: str) -> dict:
    o = store.get("orders", id=order_id)
    if o is None:
        raise KeyError(order_id)
    return o.get("extras") or {}


def _save(order_id: str, extras: dict):
    store.update("orders", {"id": order_id}, {"extras": extras, "updated": store.now()})


def _mask_mobile(m: str) -> str:
    return "•" * max(len(m) - 4, 0) + m[-4:]


def start(order_id: str, mobile: str) -> dict:
    digits = "".join(ch for ch in mobile if ch.isdigit())[-10:]
    if len(digits) != 10:
        raise DigiLockerError("Enter a 10-digit mobile number linked to DigiLocker.")
    ex = _extras(order_id)
    ex["digilocker"] = {"txn": secrets.token_hex(4), "mobile": _mask_mobile(digits), "authorised": False, "started": store.now()}
    _save(order_id, ex)
    store.log(order_id, "digilocker_otp_sent", {"mobile": _mask_mobile(digits)})
    return {"txn": ex["digilocker"]["txn"], "sent_to": _mask_mobile(digits), "demo_otp": DEMO_OTP}


def authorise(order_id: str, otp: str) -> dict:
    ex = _extras(order_id)
    dl = ex.get("digilocker")
    if not dl:
        raise DigiLockerError("Start DigiLocker first.")
    if otp.strip() != DEMO_OTP:
        raise DigiLockerError("Incorrect OTP.")
    dl["authorised"] = True
    dl["authorised_at"] = store.now()
    _save(order_id, ex)
    store.log(order_id, "digilocker_authorised", {})
    return {"authorised": True, "available": ["gst_certificate", "udyam_certificate", "signatory_ekyc", "address_from_gst"]}


def _find_udyam(trade_name: str, state: str) -> dict | None:
    for rec in udyam_registry().values():
        if rec["state"] == state and similar(rec["enterprise_name"], trade_name, threshold=0.95):
            return rec
    return None


def fetch(order_id: str, gstin: str) -> dict:
    """Pull issuer-signed documents into the order's KYC slots."""
    ex = _extras(order_id)
    if not (ex.get("digilocker") or {}).get("authorised"):
        raise DigiLockerError("DigiLocker access not authorised.")
    v = validate_gstin(gstin)
    if not v["checksum_ok"]:
        raise DigiLockerError("That GSTIN is not valid.")
    reg = gstin_registry().get(v["gstin"])
    if reg is None:
        raise DigiLockerError("No GST registration certificate found in DigiLocker for this GSTIN.")

    fetched = []
    source = {"source": "digilocker", "unreadable": False, "blur_score": None, "rotation_deg": 0, "confidence": 1.0}

    def put(slot: str, issuer: str, fields: dict):
        store.insert("documents", {"order_id": order_id, "doc_type": slot, "uploaded": store.now(), "detected_type": slot,
                                   "quality": {**source, "issuer": issuer}, "fields": fields})
        fetched.append({"slot": slot, "issuer": issuer})

    put("gst_certificate", "GSTN", {
        "gstin": reg["gstin"], "legal_name": reg["legal_name"], "trade_name": reg["trade_name"],
        "constitution": reg["constitution"], "address": reg["principal_place_of_business"],
        "date_of_liability": reg["registration_date"], "status": reg["status"],
    })
    # The GST registration certificate is an accepted proof of business address.
    put("address_proof", "GSTN", {
        "billed_to": reg["trade_name"], "address": reg["principal_place_of_business"], "bill_date": TODAY.isoformat(),
        "document": "GST registration certificate (DigiLocker)",
    })
    ud = _find_udyam(reg["trade_name"], reg["state"])
    if ud:
        put("udyam_certificate", "Ministry of MSME", {
            "udyam_number": ud["udyam_number"], "enterprise_name": ud["enterprise_name"],
            "major_activity": ud["major_activity"], "city": ud["city"], "state": ud["state"],
            "date_of_registration": ud["date_of_registration"],
        })
    prop = proprietor_name(reg["legal_name"])
    if reg["constitution"] == "Proprietorship" and prop:
        put("signatory_id", "UIDAI e-KYC", {
            "name": prop, "designation": "Proprietor", "business_name": reg["trade_name"],
            "id_number": "XXXX-XXXX-" + hashlib.sha256(prop.encode()).hexdigest()[:4].upper(),
        })
    store.log(order_id, "digilocker_fetched", {"gstin": mask_gstin(reg["gstin"]), "docs": [f["slot"] for f in fetched]})
    missing = [s for s in ("gst_certificate", "udyam_certificate", "signatory_id", "address_proof")
               if s not in {f["slot"] for f in fetched}]
    return {"fetched": fetched, "still_needed": missing, "gstin_status": reg["status"]}


# --- e-Sign ----------------------------------------------------------------------------------

def agreement(order: dict) -> dict:
    """The customer application / agreement the owner signs: exactly what they bought, at what price."""
    q = order["quote"]
    return {
        "order_id": order["id"],
        "business": order["profile"].get("business_type"),
        "city": order["profile"].get("city"),
        "lines": [{"product": l["name"], "qty": l["quantity"], "monthly": l["monthly"], "setup": l["setup"],
                   "contract_months": l["contract_months"]} for l in q["lines"]],
        "monthly_total_incl_gst": q["totals"]["monthly_total"],
        "setup_total_incl_gst": q["totals"]["setup_total"],
        "lock_in_months": q["totals"]["lock_in_months"],
        "terms_version": "SMB-2026-07",
    }


def esign_request(order_id: str) -> dict:
    o = store.get("orders", id=order_id)
    if o is None:
        raise KeyError(order_id)
    doc = agreement(o)
    digest = hashlib.sha256(json.dumps(doc, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    ex = o.get("extras") or {}
    ex["esign"] = {"requested_at": store.now(), "document_hash": digest, "signed": False}
    _save(order_id, ex)
    return {"agreement": doc, "document_hash": digest, "demo_otp": DEMO_OTP}


def esign_verify(order_id: str, otp: str) -> dict:
    ex = _extras(order_id)
    es = ex.get("esign")
    if not es:
        raise DigiLockerError("Request e-sign first.")
    if otp.strip() != DEMO_OTP:
        raise DigiLockerError("Incorrect OTP.")
    es.update(signed=True, signed_at=store.now(), method="Aadhaar OTP e-Sign (mock)")
    _save(order_id, ex)
    store.log(order_id, "esigned", {"hash": es["document_hash"][:12]})
    return es
