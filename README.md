# Project Udyam Digital — Airtel Sync 2026 (Digital Track)

A digital-first acquisition and onboarding journey that lets a small business owner **discover the right bundle, buy it and get it activated on a phone, in their own language, with minimal human effort.**

Case: *Project Udyam Digital* (YTL Hackathon 2026, Enterprise Track A). Fictional operator **Accel Telecom** / **Accel Business**. All data is synthetic.

## Repository layout

| Path | What it is |
| --- | --- |
| `docs/PLAN.md` | Case summary, data insights, solution design, architecture and build roadmap |
| `Airtel_SYNC_Case.pdf` | Original case study and problem statement |
| `Submission Template_Sync.pptx` | Official slide template |
| `YTL_TrackA_Udyam_Digital_Data/` | Synthetic data pack: product catalogue, 5,000 leads, mock GSTIN/Udyam registries, KYC specimen documents |
| `frontend/` *(planned)* | Next.js mobile-first PWA |
| `backend/` *(planned)* | FastAPI services: advisor, rules/pricing engine, KYC, tracker, back-office |

## What we are building

1. **Advisor**: a conversational GenAI assistant (Hindi, English and regional languages, text and voice) that asks about the business and recommends a bundle with a plain-language explanation. Eligibility and prices come from a deterministic rules engine over the catalogue, never from the model.
2. **Quote and checkout**: one transparent monthly price, add-ons you can toggle, and a contract-length choice.
3. **Smart KYC**: a DPDP consent screen, document upload with extraction, GSTIN/Udyam lookups against the mock registries, and cross-document validation.
4. **Tracker**: an order status page with expected dates, so customers do not have to call support.
5. **Stretch goals**: a back-office queue for field sales and partners, a lead propensity score, and partner-assisted mode.

## Timeline

| Round | Dates |
| --- | --- |
| Case release and submission (7-slide PPT, PDF + PPT, `TeamName_CampusName`) | until 8 Nov 2026, 23:59 |
| Mentorship (finalists) | 11–15 Nov 2026 |
| Virtual presentation | 13–23 Nov 2026 |
| Grand Finale (15 min pitch + 5 min Q&A) | 20 Nov 2026 |

Approach: **prototype first**, then build the deck from what the prototype proves.

See [`docs/PLAN.md`](docs/PLAN.md) for the full plan.
