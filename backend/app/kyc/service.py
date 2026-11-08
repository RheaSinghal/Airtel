"""KYC orchestration: consent -> upload (OCR + parse) -> verify. Raw images are never persisted."""
from __future__ import annotations

from datetime import timedelta

from .. import llm, store
from ..config import CONSENT_VERSION, KYC_RETENTION_DAYS, TODAY
from ..data import gstin_registry, udyam_registry
from .identifiers import mask_gstin, mask_id, mask_udyam, validate_gstin, validate_udyam
from .ocr import BLUR_THRESHOLD, read
from . import passbook
from .parse import DOC_TYPES, classify, extract
from .validate import verify

CONSENT_TEXT = {
    "en": {
        "title": "Your consent for KYC",
        "purpose": "We use your documents only to verify your business identity and address, "
                   "as required to activate telecom services.",
        "data": ["GST certificate", "Udyam certificate", "Authorised signatory ID", "Address proof (utility bill)"],
        "how": "Documents are read on our servers. We keep only the verified details (name, GSTIN, address) "
               f"and delete the photos immediately after reading them. Verified details are kept for {KYC_RETENTION_DAYS} "
               "days after activation, or as required by telecom licence rules.",
        "rights": "You can withdraw consent and ask us to delete your data at any time from the order tracker. "
                  "Withdrawing before activation cancels the order.",
        "share": "We do not share your documents with sales partners or use them for marketing.",
    },
    "hi": {
        "title": "KYC के लिए आपकी सहमति",
        "purpose": "हम आपके डॉक्यूमेंट सिर्फ़ आपके बिज़नेस की पहचान और पता वेरिफ़ाई करने के लिए इस्तेमाल करते हैं, "
                   "जो टेलीकॉम सेवाएँ चालू करने के लिए ज़रूरी है।",
        "data": ["GST सर्टिफ़िकेट", "Udyam सर्टिफ़िकेट", "ऑथराइज़्ड साइनेटरी ID", "पते का प्रमाण (बिजली का बिल)"],
        "how": "डॉक्यूमेंट हमारे सर्वर पर पढ़े जाते हैं। हम सिर्फ़ वेरिफ़ाई की गई जानकारी (नाम, GSTIN, पता) रखते हैं "
               f"और पढ़ने के तुरंत बाद फ़ोटो डिलीट कर देते हैं। वेरिफ़ाई की गई जानकारी एक्टिवेशन के बाद {KYC_RETENTION_DAYS} "
               "दिन तक, या टेलीकॉम लाइसेंस नियमों के अनुसार, रखी जाती है।",
        "rights": "आप ऑर्डर ट्रैकर से कभी भी सहमति वापस ले सकते हैं और अपना डेटा डिलीट करवा सकते हैं। "
                  "एक्टिवेशन से पहले सहमति वापस लेने पर ऑर्डर रद्द हो जाएगा।",
        "share": "हम आपके डॉक्यूमेंट सेल्स पार्टनर के साथ शेयर नहीं करते और न ही मार्केटिंग के लिए इस्तेमाल करते हैं।",
    },
}

# Fields that identify a person or business and must be masked whenever shown back.
SENSITIVE = {"gstin": mask_gstin, "udyam_number": mask_udyam, "id_number": mask_id, "consumer_number": mask_id}


def masked_fields(fields: dict) -> dict:
    return {k: SENSITIVE[k](v) if k in SENSITIVE else v for k, v in fields.items()}


def consent_text(lang: str) -> dict:
    return {"version": CONSENT_VERSION, **CONSENT_TEXT.get(lang, CONSENT_TEXT["en"])}


def record_consent(order_id: str, accepted: bool, lang: str) -> dict:
    at = store.now()
    consent = {"version": CONSENT_VERSION, "accepted": accepted, "at": at, "lang": lang,
               "purposes": ["kyc_verification"], "withdrawn_at": None}
    if accepted:  # N2: the owner keeps a receipt tied to the exact notice they saw
        consent["receipt"] = passbook.receipt(order_id, consent_text(lang), lang, at, retention_until())
    store.update("orders", {"id": order_id}, {"consent": consent, "updated": store.now()})
    store.log(order_id, "consent", {"accepted": accepted, "version": CONSENT_VERSION})
    return consent


def process_upload(order_id: str, slot: str, data: bytes, lang: str = "en") -> dict:
    """OCR one document into the given slot. The image bytes are dropped when this returns."""
    if slot not in DOC_TYPES:
        raise ValueError(f"unknown document type {slot}")
    ocr = read(data)
    detected = classify(ocr.rows) if ocr.rows else None
    unreadable = ocr.blur_score < BLUR_THRESHOLD or (detected is None and ocr.mean_confidence < 0.9)
    fields = extract(slot, ocr.rows) if not unreadable else {}
    source = "ocr"

    # Optional: let a vision LLM fill gaps OCR could not read (never for blurred images:
    # a model guessing at an unreadable document is exactly what KYC must not accept).
    if not unreadable and llm.enabled() and _missing_key_fields(slot, fields):
        extra = llm.extract_document(slot, data)
        if extra:
            for k, v in extra.items():
                fields.setdefault(k, v)
            source = "ocr+vision"

    quality = {"blur_score": round(ocr.blur_score, 1), "rotation_deg": ocr.rotation_deg,
               "confidence": ocr.mean_confidence, "unreadable": unreadable, "source": source}
    store.insert("documents", {"order_id": order_id, "doc_type": slot, "uploaded": store.now(),
                               "detected_type": detected, "quality": quality, "fields": fields})
    store.log(order_id, "document_uploaded", {"slot": slot, "detected": detected, "unreadable": unreadable})
    return {"slot": slot, "detected_type": detected, "quality": quality, "fields": masked_fields(fields)}


def _missing_key_fields(slot: str, fields: dict) -> bool:
    key = {"gst_certificate": "gstin", "udyam_certificate": "udyam_number",
           "signatory_id": "name", "address_proof": "bill_date"}[slot]
    return not fields.get(key)


def run_verification(order_id: str, lang: str = "en", has_udyam: bool | None = None) -> dict:
    docs = {d["doc_type"]: d for d in store.select("documents", "order_id = ?", (order_id,))}
    result = verify(docs, lang=lang, has_udyam=has_udyam)
    result["verified_at"] = store.now()
    store.update("orders", {"id": order_id}, {"kyc": result, "updated": store.now()})
    store.log(order_id, "kyc_verified", {"verdict": result["verdict"]})
    return result


def withdraw(order_id: str):
    """DPDP: withdraw consent -> delete extracted document data, keep only an audit record."""
    store.delete("documents", order_id=order_id)
    order = store.get("orders", id=order_id)
    consent = (order or {}).get("consent") or {}
    consent["withdrawn_at"] = store.now()
    store.update("orders", {"id": order_id}, {"consent": consent, "kyc": None, "updated": store.now()})
    store.log(order_id, "consent_withdrawn", {})


def retention_until() -> str:
    return (TODAY + timedelta(days=KYC_RETENTION_DAYS)).isoformat()


# --- Mock registry APIs ---------------------------------------------------------------------

def lookup_gstin(raw: str) -> dict:
    v = validate_gstin(raw)
    out = {"gstin": mask_gstin(v["gstin"]), "format_ok": v["format_ok"], "checksum_ok": v["checksum_ok"],
           "state": v["state"], "found": False}
    if v["checksum_ok"]:
        reg = gstin_registry().get(v["gstin"])
        if reg:
            out.update(found=True, legal_name=reg["legal_name"], trade_name=reg["trade_name"],
                       constitution=reg["constitution"], state=reg["state"], status=reg["status"],
                       registration_date=reg["registration_date"],
                       address=reg["principal_place_of_business"])
    return out


def lookup_udyam(raw: str) -> dict:
    v = validate_udyam(raw)
    out = {"udyam_number": mask_udyam(v["udyam_number"]), "format_ok": v["format_ok"], "found": False}
    reg = udyam_registry().get(v["udyam_number"]) if v["format_ok"] else None
    if reg:
        out.update(found=True, enterprise_name=reg["enterprise_name"], enterprise_type=reg["enterprise_type"],
                   major_activity=reg["major_activity"], state=reg["state"], city=reg["city"],
                   date_of_registration=reg["date_of_registration"])
    return out
