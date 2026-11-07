# Project Udyam Digital: Plan

## 1. The problem

Accel Business sells broadband, SIMs, WhatsApp/SMS, cloud, security and CCTV to MSMEs **one product at a time**, through a field force built for large accounts:

- Needs are discovered in a sales visit, and reps pitch whatever is on target that month
- A quote takes 3–5 days and arrives as a PDF of product codes
- KYC (GST certificate, Udyam, address proof, signatory ID) is collected on paper or by email
- Installation takes 10–14 days, with 3–4 follow-up calls from the customer
- Each product is billed and supported separately

**Goal:** a digital-first journey where an owner discovers the right bundle, buys it and gets it activated, on a phone, in their preferred language.

### Key questions the case asks

1. Which MSME segments come first, and which bundle (products, price, contract) fits each?
2. How does needs discovery work without a salesperson? (conversational advisor, Hindi and regional languages)
3. How is KYC made near-instant (GSTIN/Udyam lookup, OCR, DigiLocker, e-sign) while complying with the DPDP Act 2023?
4. How do the field force and channel partners fit, so digital adds to them instead of competing?
5. Which 3–5 success metrics matter, and what targets do we set?

### Deliverables

- **Round 1 (by 8 Nov):** 7-slide PPT covering approach, competitive analysis and impact
- **Full case:** working prototype (3-minute demo video and repo), architecture diagram, business case (10 slides or fewer), 1-page privacy and security note

Judges hold a separate pack: **15 advisor test scenarios run live during the demo**, a **KYC answer key**, and **signals planted in the leads data**. The design must be robust to all three.

## 2. Data insights (from `smb_leads.csv`, Apr–Jun 2026)

Funnel: 5,000 leads → 3,406 contacted → 1,974 needs assessed → 861 quote accepted → 588 KYC complete → **368 activated (7.4%)**. On average, 17.6 days from lead to activation, 3 status chases per customer and about ₹15k acquisition cost per activation.

### Segment economics

| Segment | Leads | Conversion | Acquisition cost per activation | Median monthly bundle | 6-month churn |
| --- | --- | --- | --- | --- | --- |
| Micro retail & services | 2,709 | 4.1% | ₹20.0k | ₹2,470 | 22.7% |
| Professional offices | 1,247 | 11.1% | ₹10.7k | ₹6,575 | 13.8% |
| Small multi-site | 755 | 11.0% | ₹15.6k | ₹28,080 | 10.8% |
| Small manufacturers | 289 | 12.8% | ₹15.3k | ₹15,910 | 8.1% |

### Findings

1. **Micro businesses lose money under field sales.** It costs about ₹20k to acquire a customer paying about ₹2.5k a month, and 23% churn. Only a self-serve channel makes this segment viable.
2. **Professional offices are the best digital beachhead:** highest conversion, lowest acquisition cost, medium price sensitivity.
3. **Needs discovery is broken.** Only 46% of activated customers bought something that overlapped with what they originally asked about.
4. **About 1,950 leads are lost to contact and visit friction:** unreachable (805), no time for a visit (531), invalid number (319), visit not scheduled (296). Self-serve removes these.
5. **About 1,000 leads are lost at the quote stage:** price too high (414), competitor cheaper (207), quote too complex (206), quote too slow (179). An instant, transparent, toggleable quote addresses these.
6. **About 270 leads are lost at KYC:** missing GST or Udyam document (94), paperwork too long (79), signatory unavailable (53), details mismatch (47).
7. **Status chasing predicts churn.** 1 follow-up call: 6% churn, NPS 7.5. 5 calls: 28% churn, NPS 6.0. This justifies the tracker.
8. **Compliance leak:** 22 activations happened on **cancelled or suspended GSTINs**. Smart KYC must block these.
9. **GSTIN matters:** leads with a GSTIN activate at 9.6% versus 2.0% without. The advisor needs a no-GSTIN path that uses only products where `requires_gstin = N`.
10. **Channels:** referrals convert at 14.8% at low cost, WhatsApp campaigns at only 2.8%, and website forms have the cheapest cost per lead (₹274).

## 3. Solution

### Core design principle

> **The LLM converses and explains; deterministic code decides.**
> Eligibility (city tier, employee count, sites, GSTIN, `requires_one_of` dependencies) and pricing are computed by a rules engine over `product_catalogue.csv`. The LLM collects the business profile, calls the engine as a tool, and explains the result in the owner's language. No hallucinated prices or ineligible products, which is critical for the 15 live judge scenarios.

### Segment strategy

| Segment | Channel | Starter bundle idea | Contract |
| --- | --- | --- | --- |
| Micro retail | 100% self-serve, partner-assisted option | AirFiber/Fibre 100 + Postpaid 299 + Cloud POS + WhatsApp Starter (GSTIN) + CCTV | 12 months (6-month AirFiber option) |
| Professional offices (**beachhead**) | Self-serve | Fibre 300 + Cloud Email + Backup + Endpoint Security + Static IP | 12 months |
| Small multi-site | Advisor, then field-sales handoff | Per-site Fibre + Failover + SD-WAN + Managed Firewall + CCTV, one bill | 24 months |
| Small manufacturers | Advisor, then field/partner | Leased Line + Machine IoT + Firewall + Postpaid lines | 24 months |

### Prototype modules

1. **Advisor (GenAI)**
   - 5–7 adaptive questions: business type, employees, sites, city, current internet and provider, spend, GSTIN/Udyam, needs
   - Languages: Hindi, English and at least one regional language; voice input through the browser speech API
   - Output: 3 tiers (Essential, Recommended, Pro), each with a "why this" explanation in plain language and the savings against current spend
   - Tool calls: `check_eligibility`, `build_bundle`, `price_quote`, `lookup_gstin`
2. **Quote and checkout**
   - Single monthly price (GST-inclusive), one-time setup fees shown separately, add-ons you can toggle, contract-length choice
   - Dependency enforcement (for example, CCTV needs a connectivity product)
   - Shareable quote link; mock payment
3. **Smart KYC**
   - DPDP consent screen first: purpose, data list, retention period, option to withdraw
   - GSTIN lookup that pre-fills legal name and address, so the owner uploads less
   - Document upload, then extraction (vision model / OCR), then validation:
     - GSTIN format and checksum (accept `X` as the 4th PAN character)
     - Registry status: Active, Cancelled or Suspended (block the last two)
     - Name and address consistency across GST, Udyam, ID and address proof
     - Address proof no older than 90 days (today = 2026-07-15)
     - Udyam number format and registry match
     - Block products with `requires_gstin = Y` when the GSTIN is invalid
   - Identifiers masked in the UI and logs
4. **Order tracker**
   - Stages: Order placed → KYC verified → Feasibility → Installation scheduled → Installed → Activated
   - Expected dates per product from `typical_install_days`
   - Proactive WhatsApp/SMS-style notifications (mocked)
5. **Back office (stretch)**
   - Queue of leads the advisor could not close, with the reason and the conversation summary
   - Propensity score (logistic regression trained on `smb_leads.csv`) to rank which leads to call
   - Routing: field sales for multi-site and manufacturers, channel partners for micro, with partner attribution

### Architecture

```
 Phone (PWA, Next.js)
   ├── Advisor chat / voice ──► FastAPI /advisor ──► LLM (tool calling)
   │                                   │                 │
   │                                   └──► Rules & Pricing Engine ◄── product_catalogue
   ├── Quote & Checkout ──────► /quote, /order
   ├── Smart KYC ─────────────► /kyc/consent, /kyc/upload ──► Extraction (vision/OCR)
   │                                   └──► Validators ──► Mock GSTIN / Udyam registry APIs
   └── Tracker ───────────────► /orders/{id}/status
 Back-office (web) ───────────► /leads, /leads/score ──► Propensity model (smb_leads)
 Storage: SQLite (prototype), documents encrypted at rest, auto-purged after verification
```

### Tech stack

- **Frontend:** Next.js (App Router), TypeScript, Tailwind, PWA, i18n
- **Backend:** Python FastAPI, Pydantic, SQLite
- **AI:** LLM with tool calling for the advisor; vision model for document extraction (provider configurable through environment variables)
- **ML:** scikit-learn for the propensity score
- **Data:** the CSVs in `YTL_TrackA_Udyam_Digital_Data/`

### Privacy (DPDP Act 2023)

- Explicit, purpose-specific consent before KYC; consent can be withdrawn
- Data minimisation: GSTIN lookup pre-fills data instead of asking for more documents; collect only what each step needs
- Masked identifiers (GSTIN, ID numbers) in the UI and logs
- Document retention: delete raw images after verification and keep only extracted, verified fields
- Role-based back-office access; partners see only their own leads

### Success metrics

| Metric | Today | Target |
| --- | --- | --- |
| Lead-to-activation conversion | 7.4% | 12% or more |
| Time to activate | 17.6 days | 7 days or less |
| Acquisition cost per activation | ~₹15,000 | ₹6,000 or less |
| Status follow-up calls per customer | 3 | 1 or fewer |
| 6-month churn | ~15% | 10% or less |

## 4. Roadmap

### Phase 1: Prototype

- [x] Repo scaffold: `backend/` (FastAPI) and `frontend/` (Next.js)
- [x] Load the CSVs into SQLite; mock GSTIN and Udyam lookup APIs
- [x] Rules engine: eligibility, dependencies, pricing, bundle tiers
- [x] Advisor: LLM tool-calling loop, multilingual prompts, voice input
- [x] Quote and checkout UI with add-on toggles
- [x] Smart KYC: consent screen, upload, extraction, validators; test against K01–K12
- [x] Order tracker
- [x] Back office: lead queue and propensity score
- [x] Test the advisor against self-written scenarios covering all segments, edge cases and no-GSTIN leads

### Phase 2: Submission materials

- [ ] Round 1: 7-slide PPT (approach, competitive analysis, impact), PDF + PPT, `TeamName_CampusName`
- [ ] Architecture diagram
- [ ] 3-minute demo video
- [ ] Business case (10 slides or fewer)
- [ ] 1-page privacy and security note
