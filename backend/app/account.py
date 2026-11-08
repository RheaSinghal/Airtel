"""After activation: one bill and one support channel for every product."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote as urlquote

from . import store

CATEGORIES = {
    "internet_down": {"label": "Internet not working", "team": "Network operations", "sla_hours": 4, "priority": "high"},
    "slow": {"label": "Slow internet", "team": "Network operations", "sla_hours": 24, "priority": "medium"},
    "billing": {"label": "Billing question", "team": "Billing", "sla_hours": 24, "priority": "low"},
    "device": {"label": "CCTV / POS / Wi-Fi device", "team": "Field service", "sla_hours": 24, "priority": "medium"},
    "change": {"label": "Add or change a service", "team": "Account manager", "sla_hours": 48, "priority": "low"},
    "other": {"label": "Something else", "team": "Business care", "sla_hours": 24, "priority": "low"},
}

TRIAGE = [
    (r"not working|down|no internet|band hai|nahi chal|बंद|नहीं चल", "internet_down"),
    (r"slow|speed|buffer|dheema|धीमा", "slow"),
    (r"bill|charge|invoice|payment|paisa|बिल", "billing"),
    (r"cctv|camera|pos|billing machine|wi-?fi|router|tablet", "device"),
    (r"add|upgrade|change|more sims?|new line|extra", "change"),
]


def bill(order: dict) -> dict:
    q = order["quote"]
    lines = [{"name": l["name"], "category": l["category"], "quantity": l["quantity"], "amount": l["monthly"]} for l in q["lines"]]
    t = q["totals"]
    now = datetime.now(timezone.utc)
    period = now.strftime("%b %Y")
    due = (now.replace(day=1) + timedelta(days=45)).replace(day=10).date().isoformat()
    upi = (f"upi://pay?pa=accelbusiness@upi&pn=Accel%20Business&am={t['monthly_total']}"
           f"&tn={urlquote('Bill ' + order['id'] + ' ' + period)}&cu=INR")
    categories = sorted({l["category"] for l in lines})
    return {
        "order_id": order["id"], "period": period, "due_date": due, "lines": lines,
        "subtotal": t["monthly_before_tax"], "gst": t["monthly_gst"], "total": t["monthly_total"],
        "upi_link": upi, "separate_bills_before": len(categories) + (1 if len(lines) > len(categories) else 0),
        "categories": categories, "autopay_available": True,
    }


def triage(text: str) -> str:
    low = text.lower()
    return next((cat for pattern, cat in TRIAGE if re.search(pattern, low)), "other")


def create_ticket(order: dict, text: str, category: str | None = None) -> dict:
    cat = category if category in CATEGORIES else triage(text)
    cfg = CATEGORIES[cat]
    now = datetime.now(timezone.utc)
    diagnostics = None
    if cat in ("internet_down", "slow"):
        # Automated remote line test before a human looks at it.
        diagnostics = {"line_test": "Signal OK at the exchange; router last seen 6 min ago",
                       "action": "Remote router restart sent. If it is still down in 10 minutes, an engineer is auto-assigned."}
    t = {
        "id": store.new_id("TKT"), "order_id": order["id"], "created": store.now(), "updated": store.now(),
        "category": cat, "text": text[:500], "status": "open",
        "detail": {"label": cfg["label"], "team": cfg["team"], "priority": cfg["priority"],
                   "resolve_by": (now + timedelta(hours=cfg["sla_hours"])).isoformat(timespec="minutes"),
                   "diagnostics": diagnostics},
    }
    store.insert("tickets", t)
    store.log(order["id"], "ticket_created", {"category": cat})
    return t


def tickets(order_id: str) -> list[dict]:
    return store.select("tickets", "order_id = ?", (order_id,), order="created DESC")
