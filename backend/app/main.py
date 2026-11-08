"""Project Udyam Digital API."""
from __future__ import annotations

import logging

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import backoffice, impact, llm, orders, scenarios, store, whatsapp
from .advisor import flow
from .config import CORS_ORIGINS, DATA_DIR, KYC_RETENTION_DAYS, TODAY, WA_VERIFY_TOKEN
from .data import catalogue, cities
from .engine.offer import build_offer
from .engine.pricing import CONTRACT_OPTIONS, quote
from .engine.profile import BusinessProfile
from .engine.rules import check_bundle
from .i18n import LANGS, block_text
from .kyc import digilocker
from .kyc import service as kyc
from .kyc.parse import DOC_TYPES

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Udyam Digital API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

MAX_UPLOAD_BYTES = 8 * 1024 * 1024


@app.get("/api/health")
def health():
    return {"ok": True, "llm": llm.enabled(), "today": TODAY.isoformat()}


@app.get("/api/meta")
def meta():
    return {"languages": LANGS, "contract_options": list(CONTRACT_OPTIONS), "cities": sorted(cities()),
            "llm": llm.enabled(), "retention_days": KYC_RETENTION_DAYS}


@app.get("/api/catalogue")
def get_catalogue():
    return [p.__dict__ for p in catalogue().values()]


# ------------------------------------------------------------------ advisor

class StartSession(BaseModel):
    lang: str = "en"
    channel: str = "web"
    partner_id: str | None = None  # set when a channel partner runs the advisor for the owner


class UserMessage(BaseModel):
    text: str | None = Field(default=None, max_length=1000)
    payload: dict | None = None
    lang: str | None = None


def _public_session(s: dict) -> dict:
    return {k: s.get(k) for k in ("id", "lang", "stage", "profile", "messages", "recommendation", "order_id", "partner_id")}


@app.post("/api/advisor/sessions")
def start_session(body: StartSession):
    lang = body.lang if body.lang in LANGS else "en"
    first = flow.start(lang)
    s = {"id": store.new_id("S"), "created": store.now(), "updated": store.now(), "lang": lang, "channel": body.channel,
         "partner_id": body.partner_id, "profile": {}, "messages": [first], "recommendation": None,
         "stage": "collecting", "order_id": None, "meta": {"expecting": "business_type", "asked": {"business_type": 1}}}
    store.insert("sessions", s)
    store.log(s["id"], "session_started", {"lang": lang, "channel": body.channel, "partner": bool(body.partner_id)})
    return _public_session(s)


@app.get("/api/advisor/sessions/{sid}")
def get_session(sid: str):
    s = store.get("sessions", id=sid)
    if not s:
        raise HTTPException(404, "session not found")
    return _public_session(s)


@app.post("/api/advisor/sessions/{sid}/messages")
def post_message(sid: str, body: UserMessage):
    s = store.get("sessions", id=sid)
    if not s:
        raise HTTPException(404, "session not found")
    if body.lang and body.lang in LANGS:
        s["lang"] = body.lang
    s["meta"] = s.get("meta") or {}
    turn = flow.Turn(s)
    new = turn.handle(body.text, body.payload)
    s["updated"] = store.now()
    store.insert("sessions", s)
    return {"messages": new, "stage": s["stage"], "profile": s["profile"], "recommendation": s.get("recommendation")}


# ------------------------------------------------------------------ quote

class QuoteRequest(BaseModel):
    profile: dict
    items: list[dict]
    contract_months: int = 12
    lang: str = "en"


@app.post("/api/quote")
def make_quote(body: QuoteRequest):
    p = BusinessProfile(**{k: v for k, v in body.profile.items() if k in BusinessProfile.model_fields})
    problems = check_bundle([(i["product_id"], int(i.get("quantity", 1))) for i in body.items], p)
    q = quote(body.items, body.contract_months, p.monthly_spend)
    for prob in problems:
        prob["message"] = block_text(prob, body.lang)
    return {**q, "problems": problems}


@app.post("/api/offer")
def make_offer(body: QuoteRequest):
    p = BusinessProfile(**{k: v for k, v in body.profile.items() if k in BusinessProfile.model_fields})
    return build_offer(p, body.lang, body.contract_months)


# ------------------------------------------------------------------ orders + tracker

class CreateOrder(BaseModel):
    session_id: str | None = None
    profile: dict
    items: list[dict]
    contract_months: int = 12
    lang: str = "en"
    contact: dict | None = None


@app.post("/api/orders")
def create_order(body: CreateOrder):
    try:
        o = orders.create(body.profile, body.items, body.contract_months, body.lang, body.session_id, body.contact)
    except orders.OrderError as e:
        for prob in e.problems:
            prob["message"] = block_text(prob, body.lang)
        raise HTTPException(422, {"problems": e.problems})
    return _public_order(o)


def _public_order(o: dict) -> dict:
    kyc_view = o.get("kyc")
    docs = store.select("documents", "order_id = ?", (o["id"],))
    return {
        "id": o["id"], "status": o["status"], "lang": o["lang"], "created": o["created"],
        "profile": o["profile"], "items": o["items"], "contract_months": o["contract_months"], "quote": o["quote"],
        "consent": o.get("consent"), "kyc": kyc_view,
        "esign": {k: v for k, v in ((o.get("extras") or {}).get("esign") or {}).items()},
        "digilocker": bool(((o.get("extras") or {}).get("digilocker") or {}).get("authorised")),
        "documents": {d["doc_type"]: {"fields": kyc.masked_fields(d["fields"] or {}), "quality": d["quality"],
                                      "detected_type": d["detected_type"], "uploaded": d["uploaded"]} for d in docs},
        "tracker": orders.tracker_view(o),
    }


@app.get("/api/orders/{oid}")
def get_order(oid: str):
    o = store.get("orders", id=oid)
    if not o:
        raise HTTPException(404, "order not found")
    return _public_order(o)


class Slot(BaseModel):
    slot: str


@app.post("/api/orders/{oid}/slot")
def choose_slot(oid: str, body: Slot):
    if not store.get("orders", id=oid):
        raise HTTPException(404, "order not found")
    return _public_order(orders.book_slot(oid, body.slot))


# ------------------------------------------------------------------ KYC

@app.get("/api/kyc/consent-text")
def consent_text(lang: str = "en"):
    return kyc.consent_text(lang)


class Consent(BaseModel):
    accepted: bool


def _order_or_404(oid: str) -> dict:
    o = store.get("orders", id=oid)
    if not o:
        raise HTTPException(404, "order not found")
    return o


@app.post("/api/orders/{oid}/consent")
def give_consent(oid: str, body: Consent):
    o = _order_or_404(oid)
    return kyc.record_consent(oid, body.accepted, o["lang"])


def _require_consent(o: dict):
    c = o.get("consent") or {}
    if not c.get("accepted") or c.get("withdrawn_at"):
        raise HTTPException(403, "consent required before KYC")


@app.post("/api/orders/{oid}/documents/{slot}")
async def upload_document(oid: str, slot: str, file: UploadFile = File(...)):
    o = _order_or_404(oid)
    _require_consent(o)
    if slot not in DOC_TYPES:
        raise HTTPException(400, "unknown document type")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "file too large (max 8 MB)")
    try:
        return kyc.process_upload(oid, slot, data, o["lang"])
    except OSError:
        raise HTTPException(400, "could not read image")


SAMPLES = sorted({p.name.split("_")[0] for p in (DATA_DIR / "kyc_documents").glob("K*_*.png")})


@app.get("/api/kyc/samples")
def kyc_samples():
    """Demo helper: the specimen applicants shipped with the data pack."""
    return SAMPLES


@app.post("/api/orders/{oid}/documents/{slot}/sample/{applicant}")
def upload_sample(oid: str, slot: str, applicant: str):
    o = _order_or_404(oid)
    _require_consent(o)
    path = DATA_DIR / "kyc_documents" / f"{applicant}_{slot}.png"
    if applicant not in SAMPLES or slot not in DOC_TYPES:
        raise HTTPException(404, "no such sample")
    if not path.exists():
        raise HTTPException(404, f"{applicant} has no {slot} in the data pack")
    return kyc.process_upload(oid, slot, path.read_bytes(), o["lang"])


class VerifyRequest(BaseModel):
    has_udyam: bool | None = None


@app.post("/api/orders/{oid}/kyc/verify")
def verify_kyc(oid: str, body: VerifyRequest):
    o = _order_or_404(oid)
    _require_consent(o)
    result = kyc.run_verification(oid, o["lang"], body.has_udyam)
    orders.on_kyc_result(oid, result["verdict"])
    # GST-dependent products cannot be activated on an unverified GSTIN: re-check the bundle.
    p = BusinessProfile(**{**o["profile"], "has_gstin": result["gst_verified"] or None,
                           "gstin_status": result.get("gstin_status")})
    blocked = [b for b in check_bundle([(i["product_id"], int(i.get("quantity", 1))) for i in o["items"]], p)
               if b["code"] in ("needs_gstin", "gstin_inactive")]
    for b in blocked:
        b["message"] = f"{catalogue()[b['product_id']].name}: {block_text(b, o['lang'])}"
    result["blocked_products"] = blocked
    return {**result, "order": _public_order(store.get("orders", id=oid))}


@app.post("/api/orders/{oid}/consent/withdraw")
def withdraw_consent(oid: str):
    _order_or_404(oid)
    kyc.withdraw(oid)
    return {"ok": True, "message": "Your documents and extracted details have been deleted."}


# ------------------------------------------------------------------ DigiLocker + e-Sign (mock)

class Mobile(BaseModel):
    mobile: str


class Otp(BaseModel):
    otp: str


class Gstin(BaseModel):
    gstin: str


def _dl(fn, *args):
    try:
        return fn(*args)
    except KeyError:
        raise HTTPException(404, "order not found")
    except digilocker.DigiLockerError as e:
        raise HTTPException(400, str(e))


@app.post("/api/orders/{oid}/digilocker/start")
def digilocker_start(oid: str, body: Mobile):
    _require_consent(_order_or_404(oid))
    return _dl(digilocker.start, oid, body.mobile)


@app.post("/api/orders/{oid}/digilocker/authorise")
def digilocker_authorise(oid: str, body: Otp):
    return _dl(digilocker.authorise, oid, body.otp)


@app.post("/api/orders/{oid}/digilocker/fetch")
def digilocker_fetch(oid: str, body: Gstin):
    return _dl(digilocker.fetch, oid, body.gstin)


@app.post("/api/orders/{oid}/esign/request")
def esign_request(oid: str):
    o = _order_or_404(oid)
    if (o.get("kyc") or {}).get("verdict") not in ("verified", "needs_attention"):
        raise HTTPException(409, "KYC must be verified before signing")
    return _dl(digilocker.esign_request, oid)


@app.post("/api/orders/{oid}/esign/verify")
def esign_verify(oid: str, body: Otp):
    return _dl(digilocker.esign_verify, oid, body.otp)


@app.get("/api/gstin/{gstin}")
def gstin_lookup(gstin: str):
    return kyc.lookup_gstin(gstin)


@app.get("/api/udyam/{number}")
def udyam_lookup(number: str):
    return kyc.lookup_udyam(number)


# ------------------------------------------------------------------ WhatsApp

@app.get("/api/whatsapp/webhook")
def wa_verify(mode: str = Query(alias="hub.mode", default=""), token: str = Query(alias="hub.verify_token", default=""),
              challenge: str = Query(alias="hub.challenge", default="")):
    if mode == "subscribe" and token == WA_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    raise HTTPException(403, "verification failed")


@app.post("/api/whatsapp/webhook")
async def wa_webhook(request: Request):
    payload = await request.json()
    for phone, text in whatsapp.parse_webhook(payload):
        whatsapp.send(phone, whatsapp.handle(phone, text))
    return {"ok": True}


class WaSimulate(BaseModel):
    phone: str = Field(default="919800000001", max_length=20)
    text: str = Field(max_length=1000)


@app.post("/api/whatsapp/simulate")
def wa_simulate(body: WaSimulate):
    """Same handler as the webhook; returns the replies instead of sending them."""
    return {"replies": whatsapp.handle(body.phone, body.text)}


# ------------------------------------------------------------------ back-office

@app.get("/api/backoffice/queue")
def bo_queue():
    return backoffice.queue()


@app.get("/api/backoffice/call-list")
def bo_call_list(limit: int = 50):
    return backoffice.historical_call_list(limit)


class ImpactRequest(BaseModel):
    levers: dict[str, float] = Field(default_factory=dict)
    digital_share: float = Field(default=0.3, ge=0, le=1)
    status_calls: float = Field(default=2.0, ge=1, le=5)


@app.post("/api/impact")
def impact_sim(body: ImpactRequest):
    return impact.simulate(body.levers or None, body.digital_share, body.status_calls)


@app.get("/api/backoffice/scenarios")
def bo_scenarios():
    return scenarios.run_all()


@app.get("/api/backoffice/insights")
def bo_insights():
    return backoffice.insights()


@app.get("/api/backoffice/orders")
def bo_orders():
    return [{"id": o["id"], "status": o["status"], "created": o["created"], "business": o["profile"].get("business_type"),
             "city": o["profile"].get("city"), "monthly": o["quote"]["totals"]["monthly_total"],
             "kyc": (o.get("kyc") or {}).get("verdict")} for o in store.select("orders", order="created DESC")]


class Advance(BaseModel):
    to: str | None = None


@app.post("/api/backoffice/orders/{oid}/advance")
def bo_advance(oid: str, body: Advance):
    try:
        return _public_order(orders.advance(oid, body.to))
    except KeyError:
        raise HTTPException(404, "order not found")
    except ValueError as e:
        raise HTTPException(409, str(e))
