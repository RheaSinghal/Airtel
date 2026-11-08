"""'Why not X?': rule-traced explanations for products that are not in the bundle."""
from __future__ import annotations

import re

from ..data import catalogue
from ..i18n import block_text
from .profile import BusinessProfile
from .rules import blocks

# How owners refer to products in chat -> product ids (most specific first)
ALIASES: list[tuple[str, list[str]]] = [
    (r"backup internet|failover|4g backup|5g backup", ["P09"]),
    (r"leased line|ill\b|dedicated (line|internet)|लीज़्ड", ["P06", "P05"]),
    (r"1 ?g(bps)?\b|gigabit|1000 ?mbps|fastest", ["P03"]),
    (r"300 ?mbps", ["P02"]),
    (r"air ?fib(er|re)|5g (fwa|broadband|wifi)", ["P04"]),
    (r"sd-?wan", ["P10"]),
    (r"static ip|fixed ip", ["P11"]),
    (r"ivr|cloud telephony|sip|phone lines?", ["P12"]),
    (r"toll ?free|1800", ["P13"]),
    (r"\bsms\b", ["P14"]),
    (r"whats ?app|व्हाट्सएप", ["P15"]),
    (r"e-?mail|office suite", ["P16"]),
    (r"cloud backup|data backup|\bbackup\b", ["P17"]),
    (r"website|domain", ["P18"]),
    (r"\bpos\b|billing", ["P19"]),
    (r"antivirus|endpoint", ["P20"]),
    (r"firewall", ["P21"]),
    (r"wi-?fi|guest network", ["P22"]),
    (r"cctv|camera|कैमरा", ["P23"]),
    (r"machine|iot", ["P24"]),
    (r"fleet|gps|vehicle", ["P25"]),
    (r"postpaid 599|599", ["P08"]),
    (r"\bsims?\b|postpaid|mobile (line|plan)", ["P07", "P08"]),
    (r"fib(er|re)|broadband", ["P02", "P01"]),
]

WHY_NOT = re.compile(r"why (not|no|isn'?t|don'?t)|kyun nahi|kyon nahi|क्यों नहीं|क्यूं नहीं|not included|where is", re.I)


def find_products(text: str) -> list[str]:
    low = text.lower()
    for pattern, ids in ALIASES:
        if re.search(pattern, low):
            return ids
    for pid, p in catalogue().items():
        if p.name.lower() in low:
            return [pid]
    return []


def trace(pid: str, p: BusinessProfile, bundle_ids: set[str], lang: str = "en") -> dict:
    prod = catalogue()[pid]
    reasons = [block_text(b.as_dict(), lang) for b in blocks(prod, p)]
    if prod.requires_one_of and not (set(prod.requires_one_of) & bundle_ids):
        reasons.append(block_text({"code": "needs_one_of"}, lang))
    return {"product_id": pid, "name": prod.name, "in_bundle": pid in bundle_ids, "eligible": not blocks(prod, p),
            "reasons": reasons, "price": f"₹{prod.price_min:,}–₹{prod.price_max:,} {prod.unit}/month"}


def why_not_list(p: BusinessProfile, bundle_ids: set[str], lang: str = "en") -> list[dict]:
    """Every product the rules block for this business, with the rule(s) that block it."""
    out = []
    for pid, prod in catalogue().items():
        if pid in bundle_ids:
            continue
        b = blocks(prod, p)
        if b:
            out.append({"product_id": pid, "name": prod.name, "reasons": [block_text(x.as_dict(), lang) for x in b]})
    return out


def answer_why(text: str, p: BusinessProfile, bundle_ids: set[str], lang: str = "en") -> str | None:
    ids = find_products(text)
    if not ids:
        return None
    traces = [trace(pid, p, bundle_ids, lang) for pid in ids]
    # Prefer what's in the bundle, then what they can buy, then explain the first blocked one.
    t = next((x for x in traces if x["in_bundle"]), None) or next((x for x in traces if x["eligible"]), None) or traces[-1]
    hi = lang == "hi"
    if t["in_bundle"]:
        return f"{t['name']} आपके बंडल में पहले से है।" if hi else f"{t['name']} is already in your bundle."
    if not t["eligible"]:
        why = "; ".join(t["reasons"])
        return f"{t['name']} शामिल नहीं है, क्योंकि {why}।" if hi else f"{t['name']} isn't included because {why}."
    if t["reasons"]:  # eligible but needs a connection in the same bundle
        return f"{t['name']}: {t['reasons'][0]}." if not hi else f"{t['name']}: {t['reasons'][0]}।"
    return (f"{t['name']} आपके लिए उपलब्ध है ({t['price']})। अगली स्क्रीन पर इसे ऐड-ऑन के रूप में जोड़ सकते हैं।" if hi
            else f"{t['name']} is available for you ({t['price']}). You didn't ask for it, but you can switch it on as an add-on on the next screen.")
