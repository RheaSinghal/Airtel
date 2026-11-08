"""N2 Data passbook (DPDP Act 2023): consent receipt + owner-visible access log.

The receipt proves *what* the owner agreed to: the SHA-256 of the exact notice shown, its version and
language, the purposes, the data items and the retention date. The access log shows every time the
system or staff touched their KYC data, built from the masked audit events.
"""
from __future__ import annotations

import hashlib
import json

from .. import store

# Audit event -> (who, what), in plain words for the owner.
EVENTS = {
    "consent": ("You", "Gave consent for KYC"),
    "document_uploaded": ("System (document reader)", "Read an uploaded document; photo deleted after reading"),
    "digilocker_authorised": ("You", "Allowed DigiLocker to share issuer-signed documents"),
    "digilocker_fetched": ("System (DigiLocker)", "Fetched GST, Udyam and e-KYC records"),
    "kyc_verified": ("System (validators)", "Checked documents against the GST and Udyam registries"),
    "esigned": ("You", "Signed the service agreement with Aadhaar OTP"),
    "backoffice_viewed": ("Accel staff (back-office)", "Viewed KYC issues to help fix them"),
    "consent_withdrawn": ("You", "Withdrew consent; documents and extracted details deleted"),
}


def notice_hash(notice: dict) -> str:
    """Hash of the exact notice text, so a later change to the wording can't be passed off as consented."""
    return hashlib.sha256(json.dumps(notice, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def receipt(order_id: str, notice: dict, lang: str, at: str, retention_until: str) -> dict:
    h = notice_hash(notice)
    return {
        "receipt_id": f"CR-{order_id}-{h[:8].upper()}",
        "notice_version": notice.get("version"),
        "notice_sha256": h,
        "language": lang,
        "purposes": ["kyc_verification"],
        "data_items": notice.get("data", []),
        "given_at": at,
        "retained_until": retention_until,
        "processor": "Accel Business (data fiduciary)",
        "withdraw": f"/api/orders/{order_id}/consent/withdraw",
    }


def access_log(order_id: str) -> list[dict]:
    rows = store.select("events", "ref = ? AND type IN ({})".format(",".join("?" * len(EVENTS))),
                        (order_id, *EVENTS), order="id ASC")
    return [{"at": r["ts"], "who": EVENTS[r["type"]][0], "what": EVENTS[r["type"]][1], "event": r["type"]}
            for r in rows]


def view(order: dict) -> dict:
    consent = order.get("consent") or {}
    return {
        "order_id": order["id"],
        "receipt": consent.get("receipt"),
        "status": "withdrawn" if consent.get("withdrawn_at") else "active" if consent.get("accepted") else "none",
        "access_log": access_log(order["id"]),
        "documents_stored": 0,  # raw images are never persisted
        "fields_stored": sorted({k for d in store.select("documents", "order_id = ?", (order["id"],))
                                 for k in (d.get("fields") or {})}),
    }
