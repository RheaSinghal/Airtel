# Code walkthrough

A guided tour for a reviewer new to the repo. Read `README.md` for the feature list and `docs/PROBLEMS.md` for how each case requirement maps to code.

## 1. Run it

```bash
cd backend && pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000     # API on :8000; works without an LLM key
python -m pytest -q                             # 63 tests, about 50 s

cd ../frontend && npm install
npm run dev                                     # http://localhost:3000, /api proxied to :8000
```

Optional LLM: copy `backend/.env.example` to `.env` and set any OpenAI-compatible endpoint. Without a key, the deterministic parser and the EN/HI templates run the whole demo. "Today" is pinned to 2026-07-15 by `APP_TODAY` in `backend/app/config.py`.

## 2. The design principle

> **The LLM talks, deterministic code decides.**

| Decision | Made by | Never by |
| --- | --- | --- |
| Which products a business may buy | `engine/rules.py` | the LLM |
| Prices and totals | `engine/pricing.py` | the LLM |
| KYC verdict | `kyc/validate.py` | the vision model (it only fills gaps OCR missed, never on blurred images) |
| Who calls a lead, and with what offer | `backoffice.py`, `recovery.py` | free text |

The LLM (`backend/app/llm.py`) has four jobs: extract facts, rephrase, explain and answer. Every function returns `None` on failure, so callers fall back. Every LLM sentence shown to an owner passes the **fact guard** (`backend/app/guard.py`).

## 3. Architecture at a glance

See `docs/ARCHITECTURE.md` for the diagram.
- **Frontend:** Next.js App Router in `frontend/src/app/`. Each journey screen is one client page, and `frontend/src/lib/api.ts` is the single typed API client.
- **Backend:** FastAPI in `backend/app/main.py`, which holds thin route handlers only. Logic lives in modules, and persistence is a small JSON-column SQLite layer (`backend/app/store.py`).

## 4. Request flow per journey step

### Advisor: `/advisor` → `POST /api/advisor/sessions/{id}/messages`
1. `main.post_message` loads the session and calls `advisor/flow.py::Turn.handle`.
2. `advisor/nlu.py::parse` extracts facts from free text (EN/Hindi/Hinglish). If an LLM is configured, `llm.extract_profile` adds to them. Code then picks the next missing slot (`SLOTS` in `flow.py`), and chips come from `advisor/text.py`.
3. A GSTIN in the chat is looked up immediately (`kyc/service.py::lookup_gstin`). A cancelled or suspended status sets `gstin_status`, which blocks GST-only products.
4. Once the profile is complete, `Turn._recommend` calls `engine/offer.py::build_offer`. That runs `engine/bundler.py::recommend` (Essential / Recommended / Pro, segment-aware needs, quantities, dependencies), `engine/pricing.py::quote` (one GST-inclusive price, "commit longer, pay less") and `engine/explain.py::why_not_list` (the rule that blocks each excluded product).
5. The explanation is the engine template, or the LLM's version **only if** `guard.vet` traces every number and product back to the engine's facts.
6. "Why not X?" questions are answered by `Turn._why_not` → `engine/explain.py::answer_why`, from rules and never from the model.

### Quote: `/quote` → `POST /api/quote`, `POST /api/orders`
- Toggling add-ons, quantities or 12/24/36 months re-prices through `pricing.quote`.
- `main.create_order` re-validates the bundle with `engine/rules.py::check_bundle` before `orders.py::create` writes it, so a tampered client can't order an ineligible bundle.
- `GET /api/feasibility` (`feasibility.py::check`) re-plans to 5G AirFiber where fibre doesn't reach.

### KYC: `/order/[id]/kyc`
1. `GET /api/kyc/consent-text` returns the DPDP notice, and the page can read it aloud (`frontend/src/lib/speech.ts::speak`).
2. `POST /api/orders/{id}/consent` → `kyc/service.py::record_consent` stores consent with a **receipt** (`kyc/passbook.py::receipt`: notice SHA-256, purposes, retention).
3. `POST /api/orders/{id}/documents/{slot}` → `kyc/service.py::process_upload`:
   - `kyc/ocr.py::read`: deskew, watermark removal, blur gate
   - `kyc/parse.py::classify` and `extract`
   - The image bytes are dropped when the function returns. Only fields are stored.
4. `POST /api/orders/{id}/kyc/verify` → `kyc/validate.py::verify` runs these checks:
   - GSTIN format and checksum with OCR repair (`kyc/identifiers.py::validate_gstin`)
   - registry status
   - Udyam
   - names and PIN across documents
   - signatory
   - 90-day address proof

   GST-dependent products are then re-checked against the verified GSTIN.
5. DigiLocker and e-Sign mocks: `kyc/digilocker.py` (OTP `123456`).
6. `POST /api/orders/{id}/consent/withdraw` → `kyc/service.py::withdraw` deletes the fields and the result.

### Tracker: `/order/[id]` → `GET /api/orders/{id}`, `GET /api/orders/{id}/passbook`
- `orders.py::plan` dates every stage from `typical_install_days`. `orders.py::tracker_view` builds the timeline and the WhatsApp-style notifications. `orders.py::book_slot` handles the self-booked installation slot.
- `kyc/passbook.py::view` returns the consent receipt and the owner-facing access log, built from masked audit events (`store.log`).
- `/account/[id]` (`account.py`) is the one bill plus the help desk with triage.

### Back-office: `/backoffice` → `/api/backoffice/*`
- `backoffice.py::model`: logistic regression on lead-time features only (no leakage), decile-calibrated, with hold-out AUC.
- `backoffice.py::queue`: sessions the advisor didn't close and KYC failures, ranked by `score_profile`, routed by `OWNER_RULES`, each with `recovery.py::playbook`.
- `backoffice.py::historical_call_list`: dropped leads worth a call back, each with a recovery playbook.
- `backoffice.py::insights` gives the funnel, segments, drop reasons and calls-vs-churn. `backoffice.py::audit` is the D4 compliance audit of past activations.
- `scenarios.py::run_all` runs the Advisor QA tab (16 scenarios) and reports fact-guard stats.
- The impact simulator is `impact.py::simulate`, behind `/impact`.

### WhatsApp: `/whatsapp`, `POST /api/whatsapp/webhook`
`whatsapp.py::handle` maps Cloud API messages onto the same `flow.Turn`. The simulator calls the exact same handler.

## 5. Where each novelty idea lives (`docs/NOVELTY.md`)

| Idea | Backend | Frontend | Tests |
| --- | --- | --- | --- |
| N1 Fact guard | `backend/app/guard.py` (`check`, `vet`, `stats`); hooked in `advisor/flow.py` (`_t`, `_recommend`, `_answer`) | Advisor QA tab: "LLM replies blocked" | `backend/tests/test_guard.py` |
| N2 Data passbook | `backend/app/kyc/passbook.py`; `kyc/service.py::record_consent`; `GET /api/orders/{id}/passbook` | `frontend/src/components/Passbook.tsx`; Listen button in `order/[id]/kyc/page.tsx` | `test_api.py::test_data_passbook_receipt_and_access_log` |
| N3 Recovery playbook | `backend/app/recovery.py` (`family`, `playbook`, `profile_from_lead`); used by `backoffice.queue` and `historical_call_list` | `RecoveryBrief` in `backoffice/page.tsx` | `backend/tests/test_recovery.py` |

## 6. Problem IDs → code

| IDs | Code |
| --- | --- |
| C1, C8, Q2, B1, D1, D5 | `advisor/`, `engine/`, `guard.py` |
| C2, B2 | `engine/pricing.py`, `frontend/src/app/quote/page.tsx` |
| C3, Q3, B3, G1–G3 | `kyc/`, `order/[id]/kyc/page.tsx` |
| C4, B4 | `orders.py`, `feasibility.py`, `order/[id]/page.tsx` |
| C5, C6 | `account.py`, `account/[id]/page.tsx` |
| C7, Q4, S2, S3 | `backoffice.py`, `recovery.py`, `backoffice/page.tsx` |
| D2, D3, Q1 | `engine/rules.py`, `engine/bundler.py`, `docs/BUSINESS_CASE.md` |
| D4 | `kyc/validate.py` (K01–K12), `backoffice.py::audit` (leads) |
| Q5, E3 | `impact.py`, `docs/BUSINESS_CASE.md` |
| S1 | `whatsapp.py`, `frontend/src/lib/speech.ts` |
| E2, E4 | `docs/ARCHITECTURE.md`, `docs/PRIVACY.md` |
| X1, P1 | `docs/DESIGN.md`, `frontend/src/app/globals.css`, `components/Header.tsx`, `components/Footer.tsx` |
| R1 | `deck/build_deck.py` → `Kernel_TIET.pptx`, `Kernel_TIET.pdf` |

## 7. Tests

| File | Covers |
| --- | --- |
| `backend/tests/test_engine.py` | Eligibility, dependencies, pricing rule, tiers, why-not traces |
| `backend/tests/test_api.py` | End-to-end API: conversations (EN/HI), cancelled GSTIN, handoff, order re-validation, KYC K01–K12 verdicts, tracker, withdraw, DigiLocker/e-Sign, WhatsApp, impact, one bill, coverage, passbook |
| `backend/tests/test_scenarios.py` | All 16 judge-style advisor scenarios pass through the real dialogue |
| `backend/tests/test_guard.py` | Fact guard unit tests, plus an end-to-end test where a "hallucinating" LLM is replaced by the template |
| `backend/tests/test_recovery.py` | Every drop reason maps to a playbook; engine-priced offers; the D4 audit counts |

The frontend has no unit tests. It is checked with `npm run build` (types) and `npx eslint src`, and every page was checked at 360 px and 1280 px (DESIGN.md §20 checklist).

## 8. The deck
- `deck/build_deck.py` builds the 7 slides on `Submission Template_Sync.pptx` with python-pptx, including the fade transitions and staggered entrance animations.
- `deck/export_pdf.ps1` exports the PDF through PowerPoint, and `deck/export_png.ps1` renders PNGs for QA.
- The plan (world, tokens, storyboard, motion) is in `deck/STORYBOARD.md`.

## 9. Known limitations
- **Mocks:** GSTIN/Udyam registries (CSV-backed), DigiLocker, Aadhaar e-Sign, UPI payment and outbound WhatsApp sends are mocked. PIN coverage is a deterministic hash, not network inventory.
- **No authentication** on the back-office or the order pages (order IDs act as bearer links). Production needs role-based access.
- **SQLite and a single process.** Fact-guard stats are in memory and reset on restart. Opening the back-office queue logs a "viewed" event in the passbook every time it loads (no de-duplication).
- **The impact simulator's days-to-activate** is the same (8.6) across presets, because it is driven by install times rather than the lever sliders.
- **Recovery offers** for multi-site profiles can mix per-site fibre with an AirFiber line, so the re-plan replaces only where the bundler allows.
- **Deck fonts:** Instrument Serif and DM Sans aren't installed on the build machine, so the deck uses Georgia and Segoe UI. The app loads the real fonts through `next/font`.
- **Demo video (E1)** is not recorded. `docs/DEMO_SCRIPT.md` has the 3-minute shot list.
