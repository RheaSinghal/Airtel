"""Turns OCR rows into typed fields for each document type."""
from __future__ import annotations

import re

DOC_TYPES = ("gst_certificate", "udyam_certificate", "signatory_id", "address_proof")

_TITLES = {
    "gst_certificate": ("gst registration", "gstin"),
    "udyam_certificate": ("udyam registration", "udyam reg"),
    "signatory_id": ("signatory", "id no"),
    "address_proof": ("electricity bill", "utility", "bill date", "consumer no"),
}

# label (lowercase, spaces removed) -> field name, per doc type
_LABELS = {
    "gst_certificate": {
        "gstin": "gstin", "legalname": "legal_name", "tradename": "trade_name",
        "constitution": "constitution", "addressofprincipal": "address", "placeofbusiness": "address",
        "dateofliability": "date_of_liability", "typeofregistration": "registration_type",
    },
    "udyam_certificate": {
        "udyamreg.number": "udyam_number", "udyamregnumber": "udyam_number", "enterprisename": "enterprise_name",
        "majoractivity": "major_activity", "city": "city", "state": "state",
        "dateofregistration": "date_of_registration",
    },
    "signatory_id": {
        "name": "name", "designation": "designation", "forbusiness": "business_name",
        "idno.": "id_number", "idno": "id_number", "validtill": "valid_till",
    },
    "address_proof": {
        "consumerno.": "consumer_number", "consumerno": "consumer_number", "billedto": "billed_to",
        "supplyaddress": "address", "billdate": "bill_date", "unitsconsumed": "units",
        "amountdue(inr)": "amount_due",
    },
}

DATE_RE = re.compile(r"(\d{4})\s*-\s*(\d{2})\s*-\s*(\d{2})")


def classify(rows: list[list[str]]) -> str | None:
    text = " ".join(" ".join(r) for r in rows[:4]).lower()
    for doc_type, keys in _TITLES.items():
        if any(k in text for k in keys[:1]):
            return doc_type
    full = " ".join(" ".join(r) for r in rows).lower()
    scores = {d: sum(k in full for k in keys) for d, keys in _TITLES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else None


def _key(label: str) -> str:
    return re.sub(r"[\s:!]", "", label.lower()).replace("principa1", "principal")


def extract(doc_type: str, rows: list[list[str]]) -> dict:
    labels = _LABELS[doc_type]
    fields: dict[str, str] = {}
    pending: str | None = None  # label seen on its own row (value expected on the next row)
    last: str | None = None     # field filled by the previous row

    def put(field: str, value: str):
        value = value.strip()
        if not value:
            return
        if field == "address" and field in fields:
            fields[field] = _join_wrapped(fields[field], value)
        else:
            fields.setdefault(field, value)

    for row in rows:
        first = _key(row[0])
        field = labels.get(first)
        if field:
            if len(row) > 1:
                put(field, " ".join(row[1:]))
                pending, last = None, field
            else:
                pending, last = field, None
            continue
        if pending:
            put(pending, " ".join(row))
            pending, last = None, pending
        elif last == "address" and len(row) == 1:
            # wrapped address continuation without a label
            fields["address"] = _join_wrapped(fields["address"], row[0])
        else:
            last = None

    for k in list(fields):
        if k.startswith("date") or k in ("bill_date", "valid_till"):
            m = DATE_RE.search(fields[k])
            fields[k] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else fields[k]
    return fields


def _join_wrapped(a: str, b: str) -> str:
    """The specimens hard-wrap long addresses mid-word ("West Be" + "ngal")."""
    if a and b and ((a[-1].isalpha() and b[0].islower()) or (a[-1].isdigit() and b[0].isdigit())):
        return a + b
    return f"{a} {b}".strip()


def pincode(address: str | None) -> str | None:
    m = re.search(r"(\d{6})\s*$", re.sub(r"\s+", "", address or "")) or re.search(r"(\d{6})", address or "")
    return m.group(1) if m else None
