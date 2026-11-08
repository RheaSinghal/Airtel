"""WhatsApp channel: the same advisor, rendered for WhatsApp.

Works with the Meta WhatsApp Cloud API webhook format. Chips become reply buttons (<= 3) or a
list (<= 10), and owners can also just type the option number. Without WA_TOKEN configured,
replies are returned to the caller (used by the in-app simulator) instead of being sent.
"""
from __future__ import annotations

import logging
import re

from . import store
from .advisor import flow
from .config import PUBLIC_APP_URL, WA_PHONE_ID, WA_TOKEN

log = logging.getLogger("whatsapp")

RESTART = re.compile(r"^\s*(hi|hello|hey|start|restart|menu|namaste|नमस्ते|हेलो|हाय)\s*[!.]*\s*$", re.I)
DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def _session_for(phone: str, text: str) -> dict:
    link = store.get("wa_sessions", phone=phone)
    s = store.get("sessions", id=link["session_id"]) if link else None
    if s is None or (RESTART.match(text) and len(s.get("messages") or []) > 1):
        lang = "hi" if DEVANAGARI.search(text) or re.search(r"namaste", text, re.I) else "en"
        first = flow.start(lang)
        s = {"id": store.new_id("S"), "created": store.now(), "updated": store.now(), "lang": lang, "channel": "whatsapp",
             "partner_id": None, "profile": {}, "messages": [first], "recommendation": None, "stage": "collecting",
             "order_id": None, "meta": {"expecting": "business_type", "asked": {"business_type": 1}, "wa_new": True}}
        store.insert("sessions", s)
        store.insert("wa_sessions", {"phone": phone, "session_id": s["id"], "updated": store.now()})
        store.log(s["id"], "session_started", {"channel": "whatsapp"})
    return s


def _resolve_option(s: dict, text: str) -> dict | None:
    """Map '2' or '1,3,4' (multi-select) or a button id to a structured payload."""
    opts = (s.get("meta") or {}).get("wa_options") or []
    if not opts:
        return None
    t = text.strip().lower()
    if t.startswith("opt:"):  # interactive button / list reply id
        idx = int(t[4:]) if t[4:].isdigit() else -1
        return opts[idx] if 0 <= idx < len(opts) else None
    nums = [int(n) for n in re.findall(r"\d+", t)] if re.fullmatch(r"[\d,\s]+", t) else []
    picked = [opts[n - 1] for n in nums if 0 < n <= len(opts)]
    if not picked:
        return None
    if (s.get("meta") or {}).get("wa_multi"):
        needs = [p["toggle_need"] for p in picked if "toggle_need" in p]
        return {"set_needs": needs} if needs else {"needs_done": True}
    return picked[0]


def _render(s: dict, messages: list[dict]) -> list[dict]:
    """Assistant messages -> WhatsApp messages: {'text', 'buttons'?, 'list'?}."""
    out = []
    meta = s.setdefault("meta", {})
    meta["wa_options"], meta["wa_multi"] = [], False
    for m in messages:
        if m.get("kind") == "chips_update":
            continue
        text = m.get("text") or ""
        rec = m.get("recommendation")
        if rec and rec.get("default"):
            tier = rec["tiers"][rec["default"]]
            lines = "\n".join(f"• {l['name']}{' ×' + str(l['quantity']) if l['quantity'] > 1 else ''}: ₹{l['monthly']:,}"
                              for l in tier["lines"])
            others = " | ".join(f"{t['label']} ₹{t['totals']['monthly_total']:,}" for k, t in rec["tiers"].items() if k != rec["default"])
            text = (f"{text}\n\n*{tier['label']}: ₹{tier['totals']['monthly_total']:,}/month* (incl. GST)\n{lines}"
                    + (f"\n\nOther options: {others}" if others else "")
                    + (f"\n\n_{' '.join(tier['notes'])}_" if tier["notes"] else ""))
        chips = m.get("chips") or []
        msg: dict = {"text": text.strip()}
        if chips:
            payloads = []
            labels = []
            for c in chips:
                p = c["payload"]
                if p.get("action") == "quote":
                    p = {"action": "quote_link"}
                payloads.append(p)
                labels.append(("✓ " if c.get("selected") else "") + c["label"])
            meta["wa_options"] = payloads
            meta["wa_multi"] = bool(m.get("multi"))
            if m.get("multi"):
                msg["text"] += "\n\n" + "\n".join(f"{i}. {l}" for i, l in enumerate(labels, 1)) + \
                               "\n\n_Reply with numbers, e.g. 1,3,4_"
            elif len(chips) <= 3:
                msg["buttons"] = [{"id": f"opt:{i}", "title": l[:20]} for i, l in enumerate(labels)]
            else:
                msg["list"] = [{"id": f"opt:{i}", "title": l[:24]} for i, l in enumerate(labels[:10])]
                msg["text"] += "\n\n" + "\n".join(f"{i}. {l}" for i, l in enumerate(labels, 1))
        out.append(msg)
    return out


def handle(phone: str, text: str) -> list[dict]:
    s = _session_for(phone, text)
    meta = s.setdefault("meta", {})
    if meta.pop("wa_new", False) and RESTART.match(text):
        replies = _render(s, s["messages"][:1])
        store.insert("sessions", {**s, "updated": store.now()})
        return replies
    payload = _resolve_option(s, text)
    if payload and payload.get("action") == "quote_link":
        link = f"{PUBLIC_APP_URL}/quote?session={s['id']}"
        replies = [{"text": f"Here is your price, with add-ons you can switch on or off, and checkout:\n{link}\n\n"
                            "Documents can be shared from DigiLocker in 30 seconds."}]
        s["updated"] = store.now()
        store.insert("sessions", s)
        return replies
    turn = flow.Turn(s)
    new = turn.handle(None if payload else text, payload)
    if payload:
        s["messages"].insert(len(s["messages"]) - len(new), {"role": "user", "text": text})
    replies = _render(s, new)
    s["updated"] = store.now()
    store.insert("sessions", s)
    return replies


def send(phone: str, replies: list[dict]):
    """Send through the WhatsApp Cloud API when configured."""
    if not (WA_TOKEN and WA_PHONE_ID):
        return
    import httpx

    url = f"https://graph.facebook.com/v20.0/{WA_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}"}
    for r in replies:
        if r.get("buttons"):
            body = {"type": "interactive", "interactive": {"type": "button", "body": {"text": r["text"][:1024]},
                    "action": {"buttons": [{"type": "reply", "reply": b} for b in r["buttons"]]}}}
        elif r.get("list"):
            body = {"type": "interactive", "interactive": {"type": "list", "body": {"text": r["text"][:1024]},
                    "action": {"button": "Choose", "sections": [{"title": "Options", "rows": r["list"]}]}}}
        else:
            body = {"type": "text", "text": {"body": r["text"][:4096]}}
        try:
            httpx.post(url, headers=headers, json={"messaging_product": "whatsapp", "to": phone, **body}, timeout=10)
        except httpx.HTTPError as e:
            log.warning("WhatsApp send failed: %s", e)


def parse_webhook(payload: dict) -> list[tuple[str, str]]:
    """Extract (phone, text) pairs from a Meta Cloud API webhook payload."""
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in (change.get("value") or {}).get("messages", []) or []:
                phone = msg.get("from")
                if msg.get("type") == "text":
                    text = msg["text"]["body"]
                elif msg.get("type") == "interactive":
                    i = msg["interactive"]
                    text = (i.get("button_reply") or i.get("list_reply") or {}).get("id", "")
                elif msg.get("type") == "button":
                    text = msg["button"].get("payload", "")
                else:
                    continue
                if phone and text:
                    out.append((phone, text))
    return out
