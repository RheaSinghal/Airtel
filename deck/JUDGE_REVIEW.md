# Judge review: Kernel_TIET (Round 1 deck + PDF)

How this review was done: each claim in `Kernel_TIET.pptx` was checked against the case (`Airtel_SYNC_Case.pdf`), then against the running code and data (`/api/backoffice/insights`, `/api/impact`, `/api/quote`, `/api/backoffice/scenarios`, `pytest`). Each slide was rendered through PowerPoint and checked by eye.

Status key: **OPEN** = to fix · **FIXED** = changed and re-checked · **USER** = needs you · **WONTFIX** = noted, with the reason.

---

## Pass 1: requirements coverage

### A. "What teams submit" (case p.3)
| # | Requirement | Where | Verdict |
| --- | --- | --- | --- |
| 1 | Working prototype: code repository | Slide 7 GitHub card → github.com/RheaSinghal/airtel (checked **public**) | ✅ |
| 1 | Working prototype: demo video, 3 min max | Not linked anywhere in the deck | **USER**: record it (`docs/DEMO_SCRIPT.md`) and add the link to the GitHub card |
| 2 | Architecture diagram with **components and data flows** | Slide 6 shows the components. The only flows are two unlabelled arrows | **R6.1 FIXED** |
| 3 | Business case, 10 slides or fewer: target customer, value, pricing or savings, rollout, risks | 7 slides. Target ✅ (S3) · pricing ✅ (S3) · rollout ✅ (S7) · risks ✅ (S7, one line) · value: the annual revenue figure is buried in a footnote, and its label is wrong (R7.1) | **R7.1 / R7.2 FIXED** |
| 4 | 1-page privacy and security note | `docs/PRIVACY.md` + the DPDP column on slide 6 | ✅ |
| — | Round 1 format: 7 slides, PPT + PDF, named TeamName_CampusName, on the official template | `Kernel_TIET.pptx` / `.pdf`, 7 slides, SYNC template | ✅ |

### B. Key questions (case p.2)
| Q | Covered on | Verdict |
| --- | --- | --- |
| Q1 Segments + bundle (products, **price point, contract length**) | S3 | ⚠ **R3.1**: the micro bundle (₹4,440) is 1.8× what micro shops actually pay (median ₹2,470, "very high" price sensitivity in case A2). **R3.2**: the contract line is inconsistent across cards. **R3.3**: the manufacturer price can't be reproduced from a named profile |
| Q2 Advisor without a salesperson, Hindi/regional | S4, S5 | ✅ |
| Q3 Near-instant KYC + DPDP (consent, purpose limitation, minimisation) | S4, S6 | ✅ claims hold, but see **C1** (the receipt date contradicts the notice) |
| Q4 Field force + partners | S5 | ✅ |
| Q5 3–5 metrics with targets | S7 | ⚠ **R7.2**: the targets follow no rule a judge can see (two are looser than the conservative simulation, two are stricter) |

### C. Build challenge (case p.2)
| Module | Built? | Shown in deck? |
| --- | --- | --- |
| Advisor / Quote / Smart KYC / Tracker | ✅ (63 tests pass, 16/16 advisor QA scenarios) | ✅ S4 |
| Stretch: voice + WhatsApp | ✅ | Mentioned in small text only |
| Stretch: back-office of unclosed leads | ✅ | S5 brief |
| Stretch: propensity score | ✅ (AUC 0.726) | S5, one clause |
| **R4.1 FIXED**: no single "4/4 modules + 3/3 stretch goals, 16/16 judge-style scenarios" proof line. Judges score against this list, so show it as a checklist. | | |

---

## Pass 1: number audit (deck vs code)
| Deck claim | Source | Result |
| --- | --- | --- |
| 7.4%, funnel 5,000→368, stage % | insights.funnel | ✅ |
| 17.6 days, 3 chases, ₹15,053 CAC | insights | ✅ |
| ₹20k vs ₹2.5k (micro CAC vs bundle) | micro CAC 20,007, median 2,470 | ✅ |
| 6% → 28% churn at 1 vs 5 calls | follow_up_vs_churn 5.9% / 27.9% | ✅ |
| 68 of 368 broke a rule, 22 on cancelled GSTINs | insights.audit | ✅ |
| Segment conversion/CAC (11.1%/₹10.7k, 4.1%/₹20.0k, 11.0%/₹28k, 12.8%/8.1%) | insights.segments | ✅ |
| ₹4,712 / ₹4,198 / ₹3,679 (prof, 12/24/36 mo) | /api/quote | ✅ |
| ₹4,440 / ₹3,791, ₹2,476 (micro) | /api/quote | ✅ |
| ₹34,904 / ₹32,780 (multi, 4 outlets) | /api/quote | ✅ |
| ₹49,357 / ₹48,384 (manufacturer) | no profile tried reproduces it (45.4k–53.0k depending on quantities) | ❌ **R3.3** |
| 3 turns on average | scenarios.avg_turns 2.9 | ✅ |
| 16 QA scenarios | 16/16 pass | ✅ |
| Propensity AUC 0.73 | 0.726 | ✅ |
| ~1,950 leads lost before contact | 805+531+319+296 = 1,951 | ✅ |
| Simulated 15.6% / ₹5,499 / 8.6 d / 2.0 / 14.3% | impact conservative preset | ✅ |
| "Cohort ARR ₹18.5 cr → ₹39.6 cr **per quarter of leads**" | `impact.simulate` multiplies by 4 quarters, so the figure is **annualised** | ❌ **R7.1** |
| 63 tests | `pytest`: 63 passed | ✅ |
| Install alone 10–14 days (S2) vs 8.6 days simulated (S7) | 8.6 = slowest catalogue install time in the bundle + 1 day. The case's 10–14 includes queueing | ⚠ **R7.3**: say so, or a judge will see a contradiction |

---

## Pass 1: findings and remarks

### Codebase
- **C1 (DPDP, high) FIXED**: The consent notice says data is kept "180 days after activation", but `kyc/service.retention_until()` computes the date from the fixed data-pack date (`APP_TODAY` = 2026-07-15), giving 2027-01-11. An order placed on 8 Nov 2026 then gets a receipt keeping data for only 64 days, and not counted from activation. That is the receipt contradicting the notice, which is the very thing N2 claims to prevent. **Fix:** compute it from the order's planned activation date + 180 days, falling back to the consent date + 180 days, and add a test.

### Slide 1 (cover)
- ✅ Template, title, team and campus are all correct. No change.

### Slide 2 (problem)
- **R2.1 FIXED**: "at the door" is vague. The data shows two leaks: ~1,950 leads lost **before the first conversation** and the 44% quote step. Name both in the title.

### Slide 3 (segments)
- **R3.1 FIXED (high)**: Micro is 55% of the base, has "very high" price sensitivity, and pays a median of ₹2,470/month. Leading with ₹4,440 invites the obvious objection. Lead with the engine's **₹2,476 starter (Fibre 100 + Cloud POS, no GSTIN needed)**, which sits at the micro median, and show ₹4,440 as the GSTIN upgrade.
- **R3.2 FIXED**: The second line under each price mixes "ready in 5 days" with "24-mo term". Use one format on every card: `24-mo: ₹X · live in N days`, so contract length (Q1) is answered the same way four times.
- **R3.3 FIXED**: The manufacturer price is not reproducible. Use QA scenario S06 (textile unit, 40 workers: Leased Line 100 + Machine IoT ×5 + Endpoint ×12), which the engine prices at ₹44,879 / ₹44,525.

### Slide 4 (journey)
- **R4.1 FIXED**: Add a build-challenge checklist strip: Advisor ✓ Quote ✓ Smart KYC ✓ Tracker ✓ · Stretch: voice & WhatsApp ✓ back-office ✓ propensity ✓ · 16/16 QA scenarios · 12/12 KYC specimens.
- **R4.2 WONTFIX (low)**: The consent and tracker screenshots show different order IDs. They are unreadable at slide size, and re-capturing needs the app running, so this waits for the next screenshot refresh.

### Slide 5 (novelty + field force)
- **R5.1 FIXED**: Each novelty card ends with a credit to other teams' hackathon projects ("After MEGHA…, DreamOps…"). In a judged deck this weakens the novelty claim and spends the line on unverifiable references. Replace each with **proof from the repo** (tests and behaviour). The credits stay in `docs/NOVELTY.md`.

### Slide 6 (architecture)
- **R6.1 FIXED (high, required item)**: Requirement #2 asks for data flows. Add four numbered flows: ① advise, ② verify (with the photo dropped), ③ track, ④ recover. Keep the components and the "scales by swapping mocks" strip.

### Slide 7 (business case)
- **R7.1 FIXED (correctness)**: The ARR label says "per quarter of leads" but the figure is annualised. Fix the label and promote the value line out of the footnote.
- **R7.2 FIXED**: Explain the targets in one line: conversion and CAC are **pilot gates set inside the conservative case**, while chases and churn are **tracker goals read from the data** (1 chase → 5.9% churn).
- **R7.3 FIXED**: Add to the footnote that days = bundle install time + same-day KYC, which reconciles slide 2 and slide 7.

### Housekeeping
- **H1 FIXED**: Rebuild the PPTX, re-export the PDF through PowerPoint, re-render the PNGs and re-inspect every slide for overflow.
- **H2 FIXED**: Bring `docs/BUSINESS_CASE.md` in line with the new micro lead price and the manufacturer bundle.

---

## Pass 2: re-judging after the fixes (rendered PNGs)
| # | Finding | Status |
| --- | --- | --- |
| P2.1 | Slide 3: the new micro bullets wrapped into the price | **FIXED**: bullets shortened to one line each |
| P2.2 | Slide 4: the checklist strip wrapped onto two lines | **FIXED**: dropped "63 tests" (it is already on slide 7) |
| P2.3 | Slide 6: flows 1 and 2 ran to three lines and overlapped flows 3 and 4 | **FIXED**: shortened to two lines each |
| P2.4 | Slide 5: the N2 screenshot still showed "Kept until 2027-01-11" (the C1 bug) next to the new "retention runs from activation" line | **FIXED**: the receipt is now drawn from the real API output (same receipt ID, because the notice hash is unchanged). The order went live 14 Nov, so data is kept until 2027-05-13 = live + 180 days, matching slide 4's tracker |

## Pass 3: final check
- All 7 slides re-rendered through PowerPoint: no overflow, no overlap, everything inside the safe area, template logos untouched.
- Every number on the slides traces to `/api/backoffice/insights`, `/api/impact`, `/api/quote` or `/api/backoffice/scenarios` (tables above). Changed prices were re-run through the engine: micro 2,476 / 2,181, manufacturer 44,879 / 44,525.
- `pytest`: 63 passed, including the new assertion that retention equals planned activation + 180 days.
- `Kernel_TIET.pdf` re-exported through PowerPoint. The PDF text shows the new content.
- `docs/BUSINESS_CASE.md` matches the deck (micro starter first, manufacturer = S06, target rule, days note).

### Still open (yours)
1. **USER: demo video.** The case asks for a demo video of 3 minutes or less. Record it from `docs/DEMO_SCRIPT.md`, then add the link under the GitHub card on slide 7 (one line in `business()` in `deck/build_deck.py`).
2. **WONTFIX R4.2:** the order IDs differ between the consent and tracker screenshots. They can't be read at slide size, so fix this at the next screenshot refresh.
3. **Upload:** re-upload both `Kernel_TIET.pptx` and `Kernel_TIET.pdf` if the portal still accepts revisions. Otherwise use this version for the mentorship and presentation rounds.
