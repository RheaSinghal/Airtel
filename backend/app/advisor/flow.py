"""Advisor dialogue manager.

The conversation is slot-filling with free text: one message can answer several questions
("I run 3 bakeries in Pune with 12 staff, no GST"). Facts come from the deterministic parser and,
when configured, an LLM; the next question is always chosen by code; the bundle always comes from
the rules engine.
"""
from __future__ import annotations

import re

from pydantic import ValidationError

from .. import llm, store
from ..data import business_types, catalogue
from ..engine.offer import build_offer
from ..engine.profile import ALL_NEEDS, BusinessProfile
from ..kyc.identifiers import validate_gstin
from ..kyc.service import lookup_gstin
from . import nlu
from .text import CHIP_PAYLOAD, CHIPS, NEED_CHIPS, NEED_LABELS, Q

SLOTS = ["business_type", "city", "employees", "sites", "current_internet", "monthly_spend", "has_gstin", "needs"]
OPTIONAL_ONCE = {"monthly_spend"}
MULTI_SEGMENT_MIN_SITES = 3
CHAIN_TYPES_SINGLE_SITE = {"Pre-school chain": "prof"}


# ------------------------------------------------------------------ language helpers

def _t(key: str, lang: str, **kw) -> str:
    base = Q.get(lang, Q["en"]).get(key) or Q["en"][key]
    text = base.format(**kw) if kw else base
    if lang not in Q and llm.enabled():
        return llm.phrase(Q["en"][key].format(**kw) if kw else Q["en"][key], lang) or text
    return text


def _chips(slot: str, lang: str, profile: BusinessProfile) -> list[dict]:
    if slot == "needs":
        labels = NEED_LABELS.get(lang, NEED_LABELS["en"])
        seg = profile.segment or "micro"
        chips = [{"label": labels[n], "payload": {"toggle_need": n}, "selected": n in profile.needs} for n in NEED_CHIPS[seg]]
        chips.append({"label": _t("done", lang), "payload": {"needs_done": True}, "primary": True})
        return chips
    labels = CHIPS.get(slot, {}).get(lang) or CHIPS.get(slot, {}).get("en") or []
    payloads = CHIP_PAYLOAD.get(slot)
    chips = []
    for i, label in enumerate(labels):
        value = payloads[i] if payloads else label
        chips.append({"label": label, "payload": {"set": {slot: value}}})
    if slot in OPTIONAL_ONCE:
        chips.append({"label": _t("skip", lang), "payload": {"skip": slot}})
    return chips


# ------------------------------------------------------------------ profile logic

def infer_segment(p: BusinessProfile) -> str | None:
    if not p.business_type:
        return p.segment
    base = business_types().get(p.business_type, p.segment or "micro")
    if base == "mfg":
        return "mfg"
    sites = p.sites or 1
    if sites >= MULTI_SEGMENT_MIN_SITES:
        return "multi"
    if base == "multi":  # a 'chain' type with only 1-2 outlets behaves like a micro business
        return CHAIN_TYPES_SINGLE_SITE.get(p.business_type, "micro")
    return base


def _merge(profile: dict, facts: dict) -> dict:
    merged = dict(profile)
    for k, v in facts.items():
        if v is None or k not in BusinessProfile.model_fields:
            continue
        if k == "needs":
            v = [n for n in v if n in ALL_NEEDS]
            merged["needs"] = list(dict.fromkeys((merged.get("needs") or []) + v))
        else:
            merged[k] = v
    return merged


def _validated(data: dict) -> BusinessProfile:
    try:
        return BusinessProfile(**data)
    except ValidationError as e:
        bad = {err["loc"][0] for err in e.errors()}
        return BusinessProfile(**{k: v for k, v in data.items() if k not in bad})


def _llm_facts(text: str, expecting: str | None, profile: dict) -> dict:
    data = llm.extract_profile(text, expecting, profile) or {}
    facts = {k: v for k, v in data.items() if v not in (None, [], "")}
    bt = facts.get("business_type")
    if bt and bt not in business_types():
        mapped = nlu.find_business_type(bt)
        if mapped:
            facts["business_type"] = mapped
        elif facts.get("segment") in ("micro", "prof", "multi", "mfg"):
            facts["business_type"] = {"micro": "Kirana store", "prof": "CA firm", "multi": "Apparel retail chain",
                                      "mfg": "Auto-parts unit"}[facts["segment"]]
            facts["business_label"] = bt
        else:
            facts.pop("business_type")
    if facts.get("city"):
        c = nlu.find_city(facts["city"])
        if c:
            facts["city"], facts["city_tier"], facts["state"] = c
        else:
            facts["city_tier"] = 2  # unknown smaller city -> tier-2 catalogue (conservative)
    if facts.get("current_internet") == "None":
        facts["current_internet"] = "None"
    return facts


# ------------------------------------------------------------------ the turn

class Turn:
    def __init__(self, session: dict):
        self.s = session
        self.lang = session.get("lang") or "en"
        self.out: list[dict] = []
        session.setdefault("profile", {})
        self.meta = session.setdefault("meta", {})

    def say(self, text: str, **extra):
        msg = {"role": "assistant", "text": text, **extra}
        self.out.append(msg)

    @property
    def profile(self) -> BusinessProfile:
        return _validated({k: v for k, v in self.s["profile"].items() if not k.startswith("_")})

    def set_profile(self, data: dict):
        p = _validated(data)
        p.segment = infer_segment(p)
        self.s["profile"] = p.model_dump()

    # -- main entry
    def handle(self, text: str | None, payload: dict | None) -> list[dict]:
        expecting = self.meta.get("expecting")
        if text:
            self.s.setdefault("messages", []).append({"role": "user", "text": text})

        if payload:
            self._apply_payload(payload)
        elif text:
            if nlu.wants_human(text):
                self._handoff("asked_for_human")
                self._save()
                return self.out
            facts = nlu.parse(text, expecting)
            if llm.enabled():
                llm_facts = _llm_facts(text, expecting, self.s["profile"])
                facts = {**llm_facts, **{k: v for k, v in facts.items() if k != "business_type_raw"}} if facts else llm_facts
                if llm_facts.get("business_label"):
                    self.meta["business_label"] = llm_facts["business_label"]
            if self.s["profile"].get("business_type") and expecting != "business_type":
                facts.pop("business_type", None)  # an answer about internet must not rename the business
            if facts.get("business_type_raw") and "business_type" not in facts:
                self.meta["business_label"] = facts["business_type_raw"]
            known_before = dict(self.s["profile"])
            self._absorb(facts)
            learned = {k for k in facts if facts[k] != known_before.get(k)} - {"business_type_raw"}
            if nlu.is_question(text) and not learned:
                self._answer(text)
                return self._continue(reask=True)
            if not learned and expecting:
                self.meta.setdefault("misses", {}).setdefault(expecting, 0)
                self.meta["misses"][expecting] += 1
                if self.meta["misses"][expecting] >= 2 and expecting not in ("business_type", "city"):
                    self.meta.setdefault("skipped", []).append(expecting)  # don't loop forever
        return self._continue()

    def _apply_payload(self, payload: dict):
        if payload.get("action") == "handoff":
            self._handoff(payload.get("reason", "asked_for_human"))
            self.meta["handoff_done"] = True
            return
        if "set" in payload:
            self._absorb(payload["set"])
        if "skip" in payload:
            self.meta.setdefault("skipped", []).append(payload["skip"])
        if "set_needs" in payload:  # the client toggles chips locally and sends the final list
            needs = [n for n in payload["set_needs"] if n in ALL_NEEDS]
            self.set_profile({**self.s["profile"], "needs": needs})
            self.meta["needs_confirmed"] = True
            self.meta["needs_open"] = False
        if "toggle_need" in payload:
            needs = list(self.s["profile"].get("needs") or [])
            n = payload["toggle_need"]
            needs.remove(n) if n in needs else needs.append(n)
            self.set_profile({**self.s["profile"], "needs": needs})
            self.meta["needs_open"] = True
        if payload.get("needs_done"):
            self.meta["needs_confirmed"] = True
            self.meta["needs_open"] = False

    def _absorb(self, facts: dict):
        facts = dict(facts)
        gstin = facts.pop("gstin", None)
        data = _merge(self.s["profile"], facts)
        if gstin:
            self._gstin(gstin, data)
        if facts.get("needs"):
            self.meta["needs_from_text"] = True
        self.set_profile(data)

    def _gstin(self, raw: str, data: dict):
        v = validate_gstin(raw)
        if not v["checksum_ok"]:
            self.say(_t("gstin_bad", self.lang))
            data["has_gstin"] = None
            return
        info = lookup_gstin(v["gstin"])
        data.update(has_gstin=True, gstin=v["gstin"])
        if info.get("found"):
            data["gstin_status"] = info["status"]
            if not data.get("city"):
                c = nlu.find_city(info.get("address", ""))
                if c:
                    data["city"], data["city_tier"], data["state"] = c
            self.say(_t("gstin_found", self.lang, name=info["trade_name"], state=info["state"], status=info["status"]))
            if info["status"] != "Active":
                self.say(_t("gstin_inactive", self.lang, status=info["status"]))

    def _next_slot(self) -> str | None:
        p = self.profile
        skipped = set(self.meta.get("skipped", []))
        for slot in SLOTS:
            if slot in skipped:
                continue
            if slot == "needs":
                if p.only_mobile or self.meta.get("needs_confirmed"):
                    continue
                return slot
            if slot in OPTIONAL_ONCE and self.meta.get("asked", {}).get(slot):
                continue
            if getattr(p, slot) is None:
                return slot
        return None

    def _continue(self, reask: bool = False) -> list[dict]:
        if self.meta.get("handoff_done"):
            self.meta.pop("handoff_done")
            self._save()
            return self.out
        slot = self._next_slot()
        if slot is None:
            if self.meta.get("needs_open"):
                slot = "needs"
            else:
                self._recommend()
                self._save()
                return self.out
        if slot == "needs" and self.meta.get("needs_open") and not reask and self.out == []:
            # a need was toggled: refresh the chips silently
            self.say("", chips=_chips("needs", self.lang, self.profile), multi=True, kind="chips_update", slot="needs")
            self._save()
            return self.out
        asked = self.meta.setdefault("asked", {})
        key = slot
        if slot == "business_type" and asked.get(slot):
            key = "business_type_retry"
        if slot == "needs" and not self.profile.needs and self.profile.segment:
            # pre-select the segment's first two needs as a starting point
            self.set_profile({**self.s["profile"], "needs": NEED_CHIPS[self.profile.segment][:2]})
        asked[slot] = asked.get(slot, 0) + 1
        self.meta["expecting"] = slot
        self.say(_t(key, self.lang), chips=_chips(slot, self.lang, self.profile), multi=slot == "needs",
                 kind="question", slot=slot)
        self._save()
        return self.out

    def _recommend(self):
        p = self.profile
        if "internet" not in p.needs and not p.only_mobile:
            p.needs = ["internet"] + list(p.needs)
        offer = build_offer(p, self.lang)
        self.s["recommendation"] = offer
        self.s["stage"] = "recommended"
        self.meta["expecting"] = None
        tier = offer["tiers"].get(offer["default"]) if offer["default"] else None
        if not tier:
            self.say(_t("fallback", self.lang))
            return
        business = self.meta.get("business_label") or p.business_type or ""
        lines = [_t("recommend_intro", self.lang, business=business.lower() if self.lang == "en" else business, city=p.city or "")]
        lines.append(_t("recommend_price", self.lang, tier=tier["label"], monthly=tier["totals"]["monthly_total"],
                        days=tier["totals"]["ready_in_days"]))
        spend = p.monthly_spend
        if spend:
            diff = tier["totals"]["monthly_before_tax"] - spend
            key = "compare_save" if diff < 0 else "compare_more"
            lines.append(_t(key, self.lang, diff=abs(diff), spend=spend, count=len(tier["lines"])))
        summary = " ".join(lines)
        explanation = None
        if llm.enabled():
            explanation = llm.explain({
                "business": business, "city": p.city, "employees": p.employees, "sites": p.sites,
                "monthly_total_incl_gst": tier["totals"]["monthly_total"], "current_spend": spend,
                "items": [{"product": l["name"], "qty": l["quantity"], "monthly": l["monthly"], "why": l["why"]} for l in tier["lines"]],
                "left_out": tier["notes"],
            }, self.lang)
        if not explanation:
            explanation = " ".join(f"• {l['name']}{' ×' + str(l['quantity']) if l['quantity'] > 1 else ''}: {l['why']}"
                                   for l in tier["lines"])
            if tier["notes"]:
                explanation += " " + " ".join(tier["notes"])
        self.say(summary, kind="recommendation", recommendation=offer, explanation=explanation)
        chips = [{"label": _t("see_quote", self.lang), "payload": {"action": "quote"}, "primary": True},
                 {"label": _t("talk_to_expert", self.lang), "payload": {"action": "handoff", "reason": "wants_expert"}}]
        if (p.sites or 1) >= 6 or (p.segment == "mfg" and (p.employees or 0) >= 25):
            self.say(_t("handoff_offer", self.lang, sites=p.sites or 1), chips=chips, kind="handoff_offer")
            self.s["handoff_suggested"] = True
        else:
            self.say(_t("next_steps", self.lang), chips=chips, kind="info")

    def _answer(self, question: str):
        cat = catalogue()
        reply = None
        if llm.enabled():
            ctx = {"profile": self.profile.model_dump(exclude_none=True),
                   "catalogue": [{"id": p.id, "name": p.name, "desc": p.description, "price": f"₹{p.price_min}-{p.price_max} {p.unit}/month",
                                  "needs_gstin": p.requires_gstin, "tiers": p.city_tiers} for p in cat.values()]}
            reply = llm.answer(question, ctx, self.lang)
        if not reply:
            low = question.lower()
            hit = next((p for p in cat.values() if any(w in low for w in re.findall(r"[a-z0-9]{3,}", p.name.lower()) if w not in ("biz", "business", "cloud"))), None)
            if hit:
                reply = f"{hit.name}: {hit.description}. ₹{hit.price_min:,}–₹{hit.price_max:,} {hit.unit}/month."
            else:
                reply = _t("fallback", self.lang)
        self.say(reply, kind="answer")

    def _handoff(self, reason: str):
        self.s["stage"] = "handoff"
        self.meta["handoff_reason"] = reason
        self.say(_t("handoff", self.lang), kind="handoff")
        store.log(self.s["id"], "handoff", {"reason": reason})

    def _save(self):
        self.s["meta"] = self.meta
        self.s.setdefault("messages", []).extend(self.out)


def start(lang: str = "en") -> dict:
    return {"role": "assistant", "text": _t("greeting", lang), "chips": _chips("business_type", lang, BusinessProfile()),
            "kind": "question", "slot": "business_type"}
