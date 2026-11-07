"""Thin wrapper over any OpenAI-compatible chat endpoint.

Design rule: the model understands and phrases; it never decides eligibility or prices.
Every function returns None on any failure so callers fall back to deterministic behaviour.
"""
from __future__ import annotations

import base64
import json
import logging
import re
from functools import lru_cache

from . import config

log = logging.getLogger("llm")


def enabled() -> bool:
    return bool(config.LLM_API_KEY)


@lru_cache
def _client():
    from openai import OpenAI

    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL, timeout=config.LLM_TIMEOUT_S, max_retries=1)


def _json_from(text: str) -> dict | None:
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def chat(messages: list[dict], model: str | None = None, json_mode: bool = False, temperature: float = 0.2) -> str | None:
    if not enabled():
        return None
    try:
        kwargs = {"model": model or config.LLM_MODEL, "messages": messages, "temperature": temperature}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = _client().chat.completions.create(**kwargs)
        return resp.choices[0].message.content
    except Exception as e:  # network, quota, unsupported response_format ...
        log.warning("LLM call failed: %s", e)
        if json_mode:  # some providers reject response_format; retry once without it
            try:
                kwargs.pop("response_format", None)
                return _client().chat.completions.create(**kwargs).choices[0].message.content
            except Exception as e2:
                log.warning("LLM retry failed: %s", e2)
        return None


LANG_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
              "bn": "Bengali", "gu": "Gujarati", "ml": "Malayalam", "pa": "Punjabi"}

PROFILE_SCHEMA = """{
  "business_type": string|null,      // e.g. "Kirana store", "Dental clinic", "Restaurant chain", "Textile unit"
  "segment": "micro"|"prof"|"multi"|"mfg"|null,
  "city": string|null,
  "employees": integer|null,
  "sites": integer|null,             // number of shops/branches/locations
  "has_gstin": boolean|null,
  "gstin": string|null,
  "has_udyam": boolean|null,
  "current_internet": "Mobile hotspot"|"Home broadband"|"Business broadband"|"Leased line"|"Mixed per site"|"None"|null,
  "current_provider": string|null,
  "monthly_spend": integer|null,     // rupees per month on telecom today
  "needs": [ "internet"|"backup_internet"|"mobile_lines"|"payments"|"messaging"|"email"|"backup"|"security"|"cctv"|"wifi"|"website"|"telephony"|"toll_free"|"static_ip"|"multi_site_mgmt"|"iot"|"fleet"|"dedicated_line" ],
  "mobile_lines": integer|null, "cameras": integer|null, "vehicles": integer|null, "machines": integer|null,
  "fibre_available": boolean|null,
  "only_mobile": boolean|null,       // true only if they explicitly want just SIMs and nothing else
  "budget": integer|null,            // rupees per month
  "is_question": boolean,            // true if the message is a question rather than an answer
  "language": "en"|"hi"|"mr"|"ta"|"te"|"kn"|"bn"|"gu"|"ml"|"pa"
}"""


def extract_profile(message: str, last_question: str | None, profile: dict) -> dict | None:
    sys = (
        "You extract structured facts about an Indian small business from the owner's chat message. "
        "The message may be in English, Hindi, Hinglish or another Indian language. "
        "Only include facts the message actually states or clearly implies; use null otherwise. "
        "Interpret short answers in the context of the last question asked. "
        "'dukaan/shop' = 1 site unless stated. 'koi GST nahi' = has_gstin false. "
        f"Return only JSON with this shape:\n{PROFILE_SCHEMA}"
    )
    user = json.dumps({"last_question": last_question, "known_profile": profile, "message": message}, ensure_ascii=False)
    return _json_from(chat([{"role": "system", "content": sys}, {"role": "user", "content": user}], json_mode=True) or "")


def phrase(text: str, lang: str, tone: str = "friendly, short, simple words a shop owner uses") -> str | None:
    """Translate/rephrase a fixed message. Facts (numbers, product names) must be preserved."""
    if lang == "en" and not tone:
        return text
    sys = (f"Rewrite the message in {LANG_NAMES.get(lang, 'English')} ({tone}). Keep every number, rupee amount and "
           "product name exactly. Do not add facts, offers or promises. Output only the rewritten message.")
    return chat([{"role": "system", "content": sys}, {"role": "user", "content": text}], temperature=0.3)


def explain(facts: dict, lang: str) -> str | None:
    sys = (
        "You are a helpful telecom advisor for Indian small businesses. Explain the recommended bundle to the owner in "
        f"{LANG_NAMES.get(lang, 'English')}, in 3-5 short sentences, plain words, no jargon. "
        "Use ONLY the facts given (products, quantities, prices, reasons, exclusions). Never invent prices, discounts or "
        "products. Mention the single monthly price and what they would stop worrying about. If something was left out, "
        "say why in one line."
    )
    return chat([{"role": "system", "content": sys}, {"role": "user", "content": json.dumps(facts, ensure_ascii=False)}], temperature=0.4)


def answer(question: str, context: dict, lang: str) -> str | None:
    sys = (
        "You answer a small-business owner's question about Accel Business telecom products. Use ONLY the catalogue and "
        "profile context given. If the answer is not in the context, say a specialist can call them. Reply in "
        f"{LANG_NAMES.get(lang, 'English')}, max 3 sentences."
    )
    return chat([{"role": "system", "content": sys},
                 {"role": "user", "content": json.dumps({"question": question, **context}, ensure_ascii=False)}])


DOC_FIELDS = {
    "gst_certificate": ["gstin", "legal_name", "trade_name", "constitution", "address", "date_of_liability"],
    "udyam_certificate": ["udyam_number", "enterprise_name", "major_activity", "city", "state", "date_of_registration"],
    "signatory_id": ["name", "designation", "business_name", "id_number", "valid_till"],
    "address_proof": ["consumer_number", "billed_to", "address", "bill_date", "amount_due"],
}


def extract_document(doc_type: str, image: bytes) -> dict | None:
    if not enabled():
        return None
    b64 = base64.b64encode(image).decode()
    sys = ("Read this Indian KYC document image. Return JSON with exactly these keys: "
           f"{DOC_FIELDS[doc_type]}. Dates as YYYY-MM-DD. Copy values character by character; if a value is missing "
           "or unreadable use null. Never guess.")
    text = chat([{"role": "system", "content": sys},
                 {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
                model=config.LLM_VISION_MODEL, json_mode=True, temperature=0)
    data = _json_from(text or "")
    return {k: str(v) for k, v in (data or {}).items() if k in DOC_FIELDS[doc_type] and v not in (None, "", "null")} or None
