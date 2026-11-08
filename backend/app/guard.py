"""Fact guard (N1): every LLM-written sentence must be traceable to engine facts.

The LLM may rephrase and translate, but any rupee amount, number of 100 or more, product ID or catalogue
product name in its output must appear in the facts the engine produced for that turn. Promotional
claims (discounts, "free") are rejected unless the facts contain them. Anything untraceable means the
caller falls back to the deterministic template, so a live demo can never show a price the engine
didn't compute, in any language.
"""
from __future__ import annotations

import json
import re
from collections import Counter

from .data import catalogue

STATS: Counter = Counter()  # checked / blocked / reason:* (exposed on the QA tab)

# Indic digits -> ASCII so "₹२,४७०" is checked like "₹2,470".
_DIGITS = {ord(c): str(i) for block in ("०१२३४५६७८९", "০১২৩৪৫৬৭৮৯", "੦੧੨੩੪੫੬੭੮੯", "૦૧૨૩૪૫૬૭૮૯",
                                         "௦௧௨௩௪௫௬௭௮௯", "౦౧౨౩౪౫౬౭౮౯", "೦೧೨೩೪೫೬೭೮೯", "൦൧൨൩൪൫൬൭൮൯")
           for i, c in enumerate(block)}
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
_PID = re.compile(r"\bP\d{2}\b")
_PROMO = re.compile(r"discount|% off|\boff\b|cashback|free of cost|for free|\bfree\b|छूट|मुफ़्त|मुफ्त|फ्री", re.I)
_TOLL_FREE = re.compile(r"toll[- ]?free", re.I)
FREE_BELOW = 100  # small counts (employees, months, days, quantities) are not prices


def _numbers(text: str) -> set[int]:
    out = set()
    for m in _NUM.findall(text.translate(_DIGITS)):
        try:
            out.add(round(float(m.replace(",", ""))))
        except ValueError:
            pass
    return out


def _flatten(facts) -> str:
    return json.dumps(facts, ensure_ascii=False) if not isinstance(facts, str) else facts


def check(text: str, facts) -> list[str]:
    """Return the list of problems; empty means the text is fully traceable to `facts`."""
    src = _flatten(facts)
    allowed = _numbers(src)
    problems = []
    for n in sorted(_numbers(text)):
        if n >= FREE_BELOW and n not in allowed:
            problems.append(f"number {n} not in engine facts")
    for pid in set(_PID.findall(text)) - set(_PID.findall(src)):
        problems.append(f"product id {pid} not in engine facts")
    low_text, low_src = text.lower(), src.lower()
    for p in catalogue().values():
        name = p.name.lower()
        if len(name) > 6 and name in low_text and name not in low_src:
            problems.append(f"product '{p.name}' not in engine facts")
    promo_text = _TOLL_FREE.sub("", text)
    if _PROMO.search(promo_text) and not _PROMO.search(_TOLL_FREE.sub("", src)):
        problems.append("promotional claim not in engine facts")
    return problems


def vet(text: str | None, facts, fallback: str, ref: str = "") -> str:
    """Return `text` if traceable, else `fallback`. Records stats either way."""
    if not text:
        return fallback
    STATS["checked"] += 1
    problems = check(text, facts)
    if not problems:
        return text
    STATS["blocked"] += 1
    for p in problems:
        STATS["reason:" + p.split(" ")[0]] += 1
    try:
        from . import store
        store.log(ref or "advisor", "fact_guard_blocked", {"problems": problems[:5]})
    except Exception:  # logging must never break a reply
        pass
    return fallback


def stats() -> dict:
    return {"checked": STATS["checked"], "blocked": STATS["blocked"],
            "reasons": {k.split(":", 1)[1]: v for k, v in STATS.items() if k.startswith("reason:")}}
