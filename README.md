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
python -m pytest -q           # 26 tests
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
