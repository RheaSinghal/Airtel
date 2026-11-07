"""Orders and the self-serve tracker."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import store
from .data import catalogue
from .engine.pricing import quote
from .engine.profile import BusinessProfile
from .engine.rules import check_bundle

STAGES = ["placed", "kyc_verified", "feasibility_ok", "install_scheduled", "installed", "activated"]

STAGE_TEXT = {
    "en": {
        "placed": ("Order placed", "We have your order and price locked in."),
        "kyc_verified": ("Documents verified", "Your KYC is complete. No paperwork left."),
        "kyc_action_needed": ("Action needed on documents", "One or more documents need attention. Open KYC to fix it."),
        "feasibility_ok": ("Site checked", "Our team confirmed fibre/wireless coverage at your address."),
        "install_scheduled": ("Installation scheduled", "An engineer is booked for your chosen slot."),
        "installed": ("Installed", "Equipment is installed and being tested."),
        "activated": ("Live!", "All services are active. Welcome to Accel Business."),
    },
    "hi": {
        "placed": ("ऑर्डर हो गया", "आपका ऑर्डर और कीमत लॉक हो गए हैं।"),
        "kyc_verified": ("डॉक्यूमेंट वेरिफ़ाई हो गए", "आपकी KYC पूरी है। अब कोई कागज़ी काम नहीं बचा।"),
        "kyc_action_needed": ("डॉक्यूमेंट पर ध्यान दें", "एक या ज़्यादा डॉक्यूमेंट ठीक करने हैं। KYC खोलकर ठीक करें।"),
        "feasibility_ok": ("साइट जाँच हो गई", "हमारी टीम ने आपके पते पर फ़ाइबर/वायरलेस कवरेज कन्फ़र्म कर दिया।"),
        "install_scheduled": ("इंस्टॉलेशन तय", "आपके चुने हुए समय पर इंजीनियर बुक है।"),
        "installed": ("इंस्टॉल हो गया", "उपकरण लग गए हैं और टेस्ट हो रहे हैं।"),
        "activated": ("चालू!", "सभी सेवाएँ चालू हैं। Accel Business में आपका स्वागत है।"),
    },
}


class OrderError(ValueError):
    def __init__(self, problems: list[dict]):
        super().__init__("bundle not allowed")
        self.problems = problems


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(d: datetime) -> str:
    return d.isoformat(timespec="minutes")


def plan(items: list[dict], start: datetime) -> dict:
    """Expected date per stage and per product, from typical_install_days (installs run in parallel)."""
    cat = catalogue()
    longest = max((cat[i["product_id"]].install_days for i in items), default=1)
    per_product = [{"product_id": i["product_id"], "name": cat[i["product_id"]].name,
                    "ready_by": _iso(start + timedelta(days=cat[i["product_id"]].install_days + 1))} for i in items]
    return {
        "kyc_verified": _iso(start + timedelta(hours=1)),
        "feasibility_ok": _iso(start + timedelta(days=1)),
        "install_scheduled": _iso(start + timedelta(days=1)),
        "installed": _iso(start + timedelta(days=longest)),
        "activated": _iso(start + timedelta(days=longest + 1)),
        "products": per_product,
    }


def create(profile: dict, items: list[dict], contract_months: int, lang: str = "en",
           session_id: str | None = None, contact: dict | None = None) -> dict:
    p = BusinessProfile(**{k: v for k, v in (profile or {}).items() if k in BusinessProfile.model_fields})
    problems = check_bundle([(i["product_id"], int(i.get("quantity", 1))) for i in items], p)
    if problems:
        raise OrderError(problems)  # the server never trusts a bundle sent by the client
    q = quote(items, contract_months, p.monthly_spend)
    start = _now()
    order_id = store.new_id("ORD")
    timeline = {
        "events": [{"stage": "placed", "at": _iso(start)}],
        "plan": plan(items, start),
        "slot": None,
        "notifications": [],
    }
    order = {
        "id": order_id, "session_id": session_id, "created": store.now(), "updated": store.now(), "lang": lang,
        "profile": p.model_dump(), "items": items, "contract_months": contract_months, "quote": q,
        "status": "placed", "consent": None, "kyc": None, "timeline": timeline, "assigned_to": None,
        "contact": contact or {},
    }
    store.insert("orders", order)
    if session_id:
        store.update("sessions", {"id": session_id}, {"stage": "ordered", "order_id": order_id, "updated": store.now()})
    notify(order, "placed")
    store.log(order_id, "order_created", {"lines": len(items), "monthly": q["totals"]["monthly_total"]})
    return order


def notify(order: dict, stage: str):
    """Proactive WhatsApp/SMS-style update, so the customer never has to call to chase status."""
    title, body = STAGE_TEXT.get(order.get("lang") or "en", STAGE_TEXT["en"]).get(stage, (stage, ""))
    order["timeline"]["notifications"].append({"at": _iso(_now()), "channel": "whatsapp", "title": title, "body": body})
    store.update("orders", {"id": order["id"]}, {"timeline": order["timeline"], "updated": store.now()})


def advance(order_id: str, to: str | None = None) -> dict:
    """Move an order to the next stage (back-office / field engineer update)."""
    order = store.get("orders", id=order_id)
    if order is None:
        raise KeyError(order_id)
    current = order["status"]
    if to is None:
        idx = STAGES.index(current) if current in STAGES else 0
        if current == "kyc_action_needed":
            raise ValueError("KYC must be fixed first")
        to = STAGES[min(idx + 1, len(STAGES) - 1)]
    order["status"] = to
    order["timeline"]["events"].append({"stage": to, "at": _iso(_now())})
    store.update("orders", {"id": order_id}, {"status": to, "timeline": order["timeline"], "updated": store.now()})
    notify(order, to)
    store.log(order_id, "stage", {"to": to})
    return store.get("orders", id=order_id)


def on_kyc_result(order_id: str, verdict: str):
    order = store.get("orders", id=order_id)
    if order is None:
        return
    if verdict in ("verified", "needs_attention") and order["status"] in ("placed", "kyc_action_needed"):
        advance(order_id, "kyc_verified")
    elif verdict == "rejected" and order["status"] in ("placed", "kyc_action_needed"):
        if order["status"] != "kyc_action_needed":
            order["status"] = "kyc_action_needed"
            order["timeline"]["events"].append({"stage": "kyc_action_needed", "at": _iso(_now())})
            store.update("orders", {"id": order_id}, {"status": "kyc_action_needed", "timeline": order["timeline"]})
            notify(order, "kyc_action_needed")


def book_slot(order_id: str, slot: str) -> dict:
    order = store.get("orders", id=order_id)
    order["timeline"]["slot"] = slot
    store.update("orders", {"id": order_id}, {"timeline": order["timeline"], "updated": store.now()})
    if order["status"] == "feasibility_ok":
        return advance(order_id, "install_scheduled")
    return store.get("orders", id=order_id)


def tracker_view(order: dict) -> dict:
    """What the owner sees: stages with done/current/expected, plain language."""
    lang = order.get("lang") or "en"
    texts = STAGE_TEXT.get(lang, STAGE_TEXT["en"])
    done = {e["stage"]: e["at"] for e in order["timeline"]["events"]}
    planned = order["timeline"]["plan"]
    status = order["status"]
    stages = []
    for st in STAGES:
        key = "kyc_action_needed" if st == "kyc_verified" and status == "kyc_action_needed" else st
        title, body = texts[key]
        state = "done" if st in done and st != status else "current" if st == status else "upcoming"
        if key == "kyc_action_needed":
            state = "blocked"
        if st == "placed":
            state = "done" if status != "placed" else "current"
        stages.append({"stage": st, "title": title, "body": body, "state": state,
                       "at": done.get(st), "expected": planned.get(st)})
    if status == "placed" and stages[1]["state"] == "upcoming":
        stages[1]["state"] = "next"
    return {
        "order_id": order["id"], "status": status, "stages": stages, "products": planned.get("products", []),
        "slot": order["timeline"].get("slot"), "notifications": order["timeline"].get("notifications", []),
        "eta": planned.get("activated"),
    }
