# Project Udyam Digital — Airtel Sync 2026 (Digital Track)

A digital-first acquisition and onboarding journey that lets a small business owner **discover the right bundle, buy it and get it activated on a phone, in their own language, with minimal human effort.**

Case: *Project Udyam Digital* (YTL Hackathon 2026, Enterprise Track A). Fictional operator **Accel Telecom** / **Accel Business**. All data is synthetic.

## What's built

| Module | What it does |
| --- | --- |
| **Advisor** (`/advisor`) | Chat or voice in 10 Indian languages. Understands free text ("मेरी जयपुर में 3 बेकरी हैं, 14 लोग") and quick-reply chips, asks only what is missing, looks up the GSTIN, and recommends Essential / Recommended / Pro bundles. Each item comes with a plain-language reason, and anything left out is explained. |
| **Rules & pricing engine** | Deterministic eligibility over `product_catalogue.csv` (city tier, size, sites, GSTIN status, product dependencies). Pricing rule: commit longer, pay less. The LLM never sets prices or eligibility. |
| **Quote & checkout** (`/quote`) | One monthly price including GST, toggleable add-ons, quantity steppers, 12/24/36-month choice, and live re-pricing. The server re-validates every bundle when an order is placed. |
| **Smart KYC** (`/order/:id/kyc`) | DPDP consent screen, on-device OCR (watermark removal, deskew, blur gate) and GSTIN checksum with OCR-error repair. Mock GSTIN/Udyam registry checks plus cross-document checks: names, PIN code, a 90-day address proof, and the signatory. Identifiers are masked, raw images are never stored, and withdrawing consent deletes the data. |
| **Tracker** (`/order/:id`) | Stages with planned dates from `typical_install_days`, per-product ready dates, self-booked install slot and proactive WhatsApp-style updates, so owners don't need to call support. |
| **Back-office** (`/backoffice`) | A queue of leads the advisor couldn't close and of KYC failures, ranked by a propensity model and routed to field sales, telesales or channel partners. Also a call-back list of historical drops and funnel insights. |
| **Partner mode** | A local reseller runs the same advisor for the owner (`/advisor?partner=CODE`) and keeps credit for the lead. |

### Beyond the brief (x-factor)

| Feature | Why it matters |
| --- | --- |
| **DigiLocker pull + Aadhaar e-Sign** (mock, OTP `123456`) | Issuer-signed GST, Udyam and e-KYC in about 30 seconds: nothing to photograph, OCR or forge. The agreement is OTP-signed with a SHA-256 document hash. A cancelled GSTIN is still rejected. |
| **WhatsApp channel** (`/whatsapp`, `/api/whatsapp/webhook`) | Meta Cloud API webhook in front of the same advisor: reply buttons and lists, numbered and multi-select replies, Hindi auto-detected. The simulator runs the exact webhook handler. |
| **"Why not X?"** | Every excluded product shows the rule that blocks it, and the advisor answers "why not leased line?" from the rules engine, never from the model. |
| **Advisor QA** (back-office tab, `pytest`) | 16 judge-style scenarios (tiers, GSTIN status, size and site limits, dependencies, no-fibre, mobile-only, Hindi) run end to end through the real dialogue. All pass, averaging 3 turns to a bundle. |
| **Impact simulator** (`/impact`) | Each fix recovers a share of the exact drop reasons it addresses in `smb_leads.csv`. Projects conversion, activations, cost per activation, days to activate, churn and ARR, with conservative, expected and ambitious presets. |
| **One-bill account** (`/account/:id`) | One consolidated GST bill with UPI pay, one help desk with free-text triage (EN/Hinglish/Hindi), SLAs and an automated line test. |
| **PIN-code coverage** | No fibre at the address: the bundle re-plans to 5G AirFiber (2-day install) and dependent products stay valid. |

### KYC results on the 12 specimen applicants

| Applicant | Verdict | Caught |
| --- | --- | --- |
| K01 | rejected | GSTIN **cancelled** in registry; Udyam number missing on certificate |
| K02 | verified | Rotated scan, auto-straightened |
| K03 | verified | Clean |
| K04 | rejected | GST certificate **too blurry**, so the owner is asked to re-upload |
| K05 | rejected | **Udyam certificate missing** |
| K06 | rejected | GSTIN **fails checksum** (one digit altered) |
| K07 | rejected | Legal name on GST certificate **doesn't match registry** |
| K08 | verified | OCR O/0 confusion repaired via checksum |
| K09, K10, K12 | verified | Clean |
| K11 | rejected | Address proof **257 days old** (limit 90) |

## Run it locally

**Backend** (Python 3.11+)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # optional: add an LLM key, the app works without one
python -m uvicorn app.main:app --port 8000
python -m pytest -q           # 50 tests
```

**Frontend** (Node 20+)

```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000; /api is proxied to :8000
```

To try it on a phone, open `http://<your-laptop-ip>:3000` on the same Wi-Fi.

**LLM (optional).** Any OpenAI-compatible endpoint (Gemini, Groq, OpenAI, OpenRouter, Ollama) can be configured in `backend/.env`. With a key, the advisor understands open-ended messages better, replies in all 10 languages and writes the explanations. Without one, English and Hindi templates plus a rule-based parser keep the demo fully working.

## Repository layout

| Path | What it is |
| --- | --- |
| `backend/app/engine/` | Profile model, eligibility rules, bundle builder, pricing, offer view |
| `backend/app/advisor/` | Dialogue manager, deterministic NLU, EN/HI text |
| `backend/app/kyc/` | OCR, parsing, identifiers, validation, consent and registry lookups |
| `backend/app/orders.py`, `backoffice.py` | Tracker and propensity model / queue / insights |
| `frontend/src/app/` | Next.js pages: landing, advisor, quote, KYC, tracker, back-office |
| `docs/PLAN.md` | Case summary, data insights, solution design, roadmap |
| `YTL_TrackA_Udyam_Digital_Data/` | Synthetic data pack |

## Timeline

| Round | Dates |
| --- | --- |
| Case release and submission (7-slide PPT, PDF + PPT, `TeamName_CampusName`) | until 8 Nov 2026, 23:59 |
| Mentorship (finalists) | 11–15 Nov 2026 |
| Virtual presentation | 13–23 Nov 2026 |
| Grand Finale (15 min pitch + 5 min Q&A) | 20 Nov 2026 |
