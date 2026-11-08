# Problem → solution map

Every problem, question and requirement in `Airtel_SYNC_Case.pdf` (and the data pack README) as one row.
One solution usually covers several rows. Solutions are named once here and referenced by name:

| Solution | What it is | Lives in |
| --- | --- | --- |
| **Advisor** | Chat/voice advisor in 10 languages; deterministic NLU + optional LLM; calls the rules engine for every bundle | `backend/app/advisor/`, `frontend/src/app/advisor/page.tsx` |
| **Engine** | Eligibility rules, bundle builder, pricing ("commit longer, pay less"), "why not X?" traces | `backend/app/engine/` |
| **Quote** | One GST-inclusive monthly price, toggleable add-ons, contract choice, server re-validation | `frontend/src/app/quote/page.tsx`, `POST /api/quote`, `POST /api/orders` |
| **Smart KYC** | DPDP consent → GSTIN pre-fill → upload/OCR → validators → registry checks; DigiLocker + e-Sign (mock) | `backend/app/kyc/`, `frontend/src/app/order/[id]/kyc/page.tsx` |
| **Tracker** | Stage timeline with planned dates from `typical_install_days`, slot booking, proactive updates | `backend/app/orders.py`, `frontend/src/app/order/[id]/page.tsx` |
| **One-bill account** | One consolidated bill, one help desk with triage and SLAs | `backend/app/account.py`, `frontend/src/app/account/[id]/page.tsx` |
| **WhatsApp** | Cloud API webhook + in-app simulator over the same advisor | `backend/app/whatsapp.py`, `frontend/src/app/whatsapp/page.tsx` |
| **Back-office** | Unclosed-lead queue, propensity model, routing to field/telesales/partner, call-back list, insights | `backend/app/backoffice.py`, `frontend/src/app/backoffice/page.tsx` |
| **Partner mode** | Reseller runs the advisor for the owner (`/advisor?partner=CODE`) and keeps credit | `frontend/src/app/advisor/page.tsx`, `store.sessions.partner_id` |
| **Impact simulator** | Recovers shares of the exact drop reasons in `smb_leads.csv`; projects conversion, CAC, days, churn | `backend/app/impact.py`, `frontend/src/app/impact/page.tsx` |
| **QA runner** | 16 judge-style advisor scenarios run end to end through the real dialogue | `backend/app/scenarios.py`, `backend/tests/test_scenarios.py` |
| **Coverage check** | PIN-code feasibility; no fibre → AirFiber re-plan | `backend/app/feasibility.py` |
| **N1 Fact guard** *(novelty)* | Every LLM sentence is checked against engine facts; any ₹ amount or product it can't trace is rejected and the template is used | `backend/app/guard.py` |
| **N2 Data passbook** *(novelty)* | DPDP consent receipt (hash, purposes, retention) + owner-visible access log + listen-aloud consent | `backend/app/kyc/passbook.py`, KYC + tracker pages |
| **N3 Recovery playbook** *(novelty)* | Per drop reason, a rules-engine re-priced recovery offer and a call brief for field sales / partners | `backend/app/recovery.py`, back-office page |
| **D4 Audit** | Historical compliance audit of activated bundles against the catalogue rules and GST registry | `backend/app/backoffice.py::audit()` |
| **Docs** | Architecture, business case, privacy note, demo script | `docs/ARCHITECTURE.md`, `docs/BUSINESS_CASE.md`, `docs/PRIVACY.md`, `docs/DEMO_SCRIPT.md` |
| **Deck** | Round 1 deck, 7 slides on the official template | `Kernel_TIET.pptx`, `Kernel_TIET.pdf` |

Status reflects the repo **after** the steps in `docs/STEPS.md`. The "Before" column records where it stood when this map was first written (commit `2285348`).

## Today's journey (case p.2)

| ID | Problem | Solution | Where it lives | Evidence | Before | Status |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | "Needs are discovered in a visit by a sales executive, who often pitches whatever is on target that month" | **Advisor** asks about the business, not a target; **Engine** recommends only from eligibility + stated needs | `/advisor`, `engine/bundler.py` | Only 46% of activated customers bought anything they originally asked about; field-sales bundles shift month to month (P07 led Apr, P08 led May–Jun). Advisor tiers are built from stated `needs` (test_engine) | done | done |
| C2 | "A quote takes 3–5 days and comes as a PDF with product codes the owner does not understand" | **Quote**: instant, plain names, one monthly price, why-this reasons | `/quote`, `engine/pricing.py`, `engine/explain.py` | 385 drops on "quote too complex" (206) + "too slow" (179); quote returned in one API call (test_api) | done | done |
| C3 | "KYC needs GST certificate, Udyam registration, address proof and signatory ID, collected physically or over email" | **Smart KYC** upload/OCR/validate + DigiLocker pull + e-Sign; GSTIN pre-fill | `/order/[id]/kyc`, `kyc/` | 12/12 specimen verdicts (README table); test_api KYC tests | done | done |
| C4 | "Installation and activation take 10–14 days on average, with 3–4 follow-up calls" | **Tracker** with dated stages, self-booked slot, proactive updates; **Coverage check** picks fastest feasible access | `/order/[id]`, `orders.py`, `feasibility.py` | 1 call → 6% churn, 5 calls → 28% (insights `follow_up_vs_churn`) | done | done |
| C5 | "Each product is billed and supported separately after activation" | **One-bill account** | `/account/[id]`, `account.py` | One bill + one ticket queue per order (test_api) | done | done |
| C6 | Owners "buy each piece from a different vendor, often from a local reseller, with no single bill or support number" | **Engine** bundles all categories; **One-bill account**; **Partner mode** keeps the local reseller in the loop | `engine/bundler.py`, `/account/[id]` | Bundles span connectivity, mobile, messaging, cloud, security, CCTV (scenarios) | done | done |
| C7 | "Cost to acquire a small business is high, conversion is low, and a large share … drop out before activation" | Self-serve **Advisor** removes visit friction; **Back-office** + **N3** recover drops; **Impact simulator** quantifies | `/impact`, `/backoffice` | 7.4% conversion, ₹15k CAC, ~1,950 contact/visit drops (insights) | partial (no recovery action per drop) | done |
| C8 | "Competitors and digital-first players are starting to offer instant online sign-up for single products" | Instant **bundle** sign-up end to end on a phone (advisor → quote → KYC → tracker in one sitting) | whole journey | QA runner: average 3 turns to a bundle | done | done |

## Key questions (case p.3)

| ID | Problem | Solution | Where it lives | Evidence | Before | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 | Which segments first, and which bundle (products, price, contract) fits each? | Professional offices beachhead, micro via self-serve + partners, multi-site/manufacturers via advisor → field; starter bundles per segment from the **Engine** | `docs/BUSINESS_CASE.md`, deck slide 3 | Segment economics: prof 11.1% conv / ₹10.7k CAC; micro 4.1% / ₹20k (insights) | partial (only in PLAN) | done |
| Q2 | Needs discovery without a salesperson: chat or voice, Hindi and regional languages, clear monthly price | **Advisor** (10 languages, voice input + read-aloud), **WhatsApp** | `/advisor`, `/whatsapp`, `advisor/nlu.py` | Hindi scenario in QA runner; 77% of leads prefer a language other than English (3,832 of 5,000) | done | done |
| Q3 | Near-instant KYC (GSTIN/Udyam lookup, OCR, DigiLocker, e-sign) while compliant with DPDP Act 2023 (consent, purpose limitation, data minimisation) | **Smart KYC** + **N2 Data passbook** | `kyc/`, `/order/[id]/kyc`, `docs/PRIVACY.md` | Raw images never stored; consent withdraw deletes data; receipt hash test | partial (no consent receipt / access log) | done |
| Q4 | Role of field force and channel partners so digital adds to them | **Partner mode**, **Back-office** routing (multi-site/mfg → field, micro → partner), **N3 Recovery playbook**, partner attribution kept on the order | `/backoffice`, `backoffice.py`, `recovery.py`, deck slide 5 | Referral converts 14.8% vs WhatsApp campaign 2.8% (insights) | partial (routing only) | done |
| Q5 | 3–5 success metrics and targets | Conversion 7.4%→12%, days 17.6→≤7, CAC ₹15k→≤₹6k, follow-up calls 3→≤1, 6-month churn ~15%→≤10%; **Impact simulator** backs each | `docs/BUSINESS_CASE.md`, `/impact`, deck slide 7 | `POST /api/impact` presets (test_api) | partial (PLAN only) | done |

## Build challenge (case p.3)

| ID | Problem | Solution | Where it lives | Evidence | Before | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Advisor: GenAI, asks type/size/locations/current tools, recommends from catalogue, explains why in plain language | **Advisor** + **Engine** + **N1 Fact guard** | `advisor/flow.py`, `engine/explain.py`, `guard.py` | 16/16 QA scenarios; guard tests | done | done |
| B2 | Quote and checkout: single transparent monthly price, toggleable add-ons | **Quote** | `/quote` | Re-price on toggle; server re-validation on order (test_api) | done | done |
| B3 | Smart KYC: upload, extraction, validation, mocked GSTIN/Udyam lookups, clear consent screen | **Smart KYC** + **N2** | `/order/[id]/kyc`, `GET /api/gstin/{g}`, `GET /api/udyam/{n}` | K01–K12 verdicts | done | done |
| B4 | Tracker the owner checks instead of calling support | **Tracker** | `/order/[id]` | Planned dates from `typical_install_days` | done | done |
| S1 | Stretch: voice or WhatsApp front end | Browser voice in **Advisor**; **WhatsApp** webhook + simulator | `/whatsapp`, `speech.ts` | Webhook tests | done | done |
| S2 | Stretch: back-office view of leads the advisor could not close | **Back-office** queue + **N3** | `/backoffice` | Queue includes handoff, abandoned, saw-offer, KYC-failed | done | done |
| S3 | Stretch: propensity score for which leads to call | Logistic regression on lead-time features only (no leakage), decile-calibrated | `backoffice.py::model` | Hold-out AUC reported in insights | done | done |

## Data signals (appendix A1–A2, data pack)

| ID | Problem | Solution | Where it lives | Evidence | Before | Status |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | Steepest drop: needs assessed → quote accepted (44%) | Instant, toggleable **Quote**; budget fit in **Engine**; **N3** re-prices quote drops | `/quote`, `recovery.py` | ~1,000 quote-stage drops: price too high 414, competitor cheaper 207, too complex 206, too slow 179 | done | done |
| D2 | Leads with GSTIN activate at 9.6% vs 2.0% without | No-GSTIN path: **Engine** offers only `requires_gstin = N` products and explains what GST registration would unlock | `engine/rules.py` | QA scenario "no GSTIN" | done | done |
| D3 | Segment needs and price sensitivity (micro UPI/POS + WhatsApp; prof uptime/email/security; multi-site one bill/central/CCTV/failover; mfg dedicated/IoT/ERP) | Segment-aware need defaults and tiers in **Engine**; budget cap | `engine/bundler.py`, `engine/profile.py` | Scenarios per segment | done | done |
| D4 | Planted problems in KYC documents (K01–K12) and in `smb_leads.csv` (judges hold answer key) | **Smart KYC** for K01–K12; **D4 Audit** for leads: inactive GSTIN activations, GSTIN-only products sold without GSTIN, tier / size / dependency violations | `kyc/validate.py`, `backoffice.py::audit`, back-office Insights tab | 22 activations on cancelled/suspended GSTIN; 11 GSTIN-only sales without GSTIN; 24 tier, 8 min-employee, 9 dependency violations | partial (leads: only inactive-GSTIN count) | done |
| D5 | 15 hidden advisor scenarios run live; never an ineligible product or a wrong price | **Engine** decides; **QA runner**; **N1 Fact guard** stops LLM text from stating a number the engine didn't produce | `scenarios.py`, `guard.py` | 16/16 scenarios pass; guard unit tests | partial (LLM text unchecked) | done |

## Submissions (case p.4)

| ID | Problem | Solution | Where it lives | Evidence | Before | Status |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Demo video (3 min max) + code repo | Repo public; shot-by-shot 3-minute **demo script** | `README.md`, `docs/DEMO_SCRIPT.md` | Script timed to 3:00 | partial | partial: recording is a manual task (needs a screen recorder and voice), script ready |
| E2 | Solution architecture diagram with components and data flows | **Docs** architecture (Mermaid + deck slide) | `docs/ARCHITECTURE.md`, deck slide 6 | — | partial (ASCII in PLAN) | done |
| E3 | Business case (≤10 slides): target customer, value, pricing/savings, rollout, risks | **Docs** business case; summarised on deck slides 3 and 7 | `docs/BUSINESS_CASE.md` | Numbers from insights + impact simulator | missing | done |
| E4 | 1-page privacy and security note | **Docs** privacy note | `docs/PRIVACY.md` | — | partial (PLAN section) | done |

## Other requirements found in the PDF / data pack

| ID | Problem | Solution | Where it lives | Evidence | Before | Status |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | "on a phone, in their preferred language" (problem statement) | 360 px-first screens; 10 languages; PWA manifest | `frontend/`, `docs/DESIGN.md §20` | Page checklist in DESIGN.md §20 | partial (no design system) | done |
| P2 | "Minimal human effort" | Self-serve end to end; humans only on handoff via **Back-office** | whole journey | — | done | done |
| R1 | Round 1: 7-slide PPT, PDF + PPT, named TeamName_CampusName | **Deck** on the official template | `Kernel_TIET.pptx`, `Kernel_TIET.pdf` | 7 slides | missing | done |
| G1 | Use 2026-07-15 as "today" for date checks (address proof ≤ 90 days) | `config.TODAY` used by validators | `config.py`, `kyc/validate.py` | K11 rejected at 257 days | done | done |
| G2 | GSTIN 4th character `X` must be accepted; Udyam district `00` | Format + checksum validator with OCR repair | `kyc/identifiers.py` | K06 checksum fail, K08 O/0 repair | done | done |
| G3 | Treat data as real: collect only what's needed, consent notice, mask identifiers in UI and logs, explain retention | **Smart KYC** masking + **N2** + **Docs** privacy note | `kyc/identifiers.py::mask_gstin`, `mask_udyam`, `mask_id`, `docs/PRIVACY.md` | Masking tests | done | done |
| G4 | Judges: technical depth and business judgement together | Prototype + business case + impact simulator | — | — | done | done |
| X1 | Frontend follows `docs/DESIGN.md` | Restyle all pages; §20 checklist | `frontend/src/app/**`, `globals.css` | §20 checklist | missing | done |
| N1–N3 | Novelty ideas from `docs/NOVELTY.md` | See solutions table | see above | tests per idea | missing | done |

## Coverage check

- Every ID above maps to at least one solution.
- Rows marked partial or missing at the start of this pass became steps in `docs/STEPS.md`: C7, Q1, Q3, Q4, Q5, D4, D5, E1, E2, E3, E4, P1, R1, X1 and N1–N3.
- Still **partial** after this pass: **E1.** The demo video has to be recorded by the team. `docs/DEMO_SCRIPT.md` gives the shot list and timing.
