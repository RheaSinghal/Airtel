"""Builds the customer-facing offer (tiers + prices + plain-language reasons) from a profile."""
from __future__ import annotations

from ..data import catalogue
from ..i18n import TIER_NAMES, note_text, reason_text
from .bundler import addon_suggestions, recommend
from .explain import why_not_list
from .pricing import quote
from .profile import BusinessProfile


def _decorate(items: list[dict], p: BusinessProfile, lang: str) -> list[dict]:
    cat = catalogue()
    out = []
    for it in items:
        prod = cat[it["product_id"]]
        out.append({**it, "name": prod.name, "category": prod.category, "description": prod.description,
                    "unit": prod.unit, "why": reason_text(it["reason"], lang, sites=p.sites or 1)})
    return out


def build_offer(p: BusinessProfile, lang: str = "en", contract_months: int = 12) -> dict:
    rec = recommend(p)
    tiers = {}
    for name, t in rec["tiers"].items():
        items = _decorate(t["items"], p, lang)
        q = quote(items, contract_months, p.monthly_spend)
        for line, item in zip(q["lines"], items):
            line.update(why=item["why"], description=item["description"], need=item.get("need"))
        tiers[name] = {
            "label": TIER_NAMES.get(lang, TIER_NAMES["en"])[name],
            "lines": q["lines"],
            "totals": q["totals"],
            "notes": [note_text(n, lang) for n in t["notes"]],
            "note_codes": t["notes"],
        }
    default = rec["default"]
    bundle_ids = {i["product_id"] for i in rec["tiers"][default]["items"]} if default else set()
    addons = _decorate(addon_suggestions(p, bundle_ids), p, lang)
    addon_quote = quote(addons, contract_months)["lines"] if addons else []
    for line, a in zip(addon_quote, addons):
        line.update(why=a["why"], description=a["description"], optional=True)
    return {"tiers": tiers, "default": default, "addons": addon_quote, "contract_months": contract_months,
            "why_not": why_not_list(p, bundle_ids, lang)}
