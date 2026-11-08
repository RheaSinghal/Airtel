# Business case: Udyam Digital

All numbers are computed from the synthetic data pack (`/api/backoffice/insights`, `/api/impact`) unless marked as an assumption.

## 1. The problem in numbers
- **7.4%** lead-to-activation (368 of 5,000). **17.6 days** to activate, **3** status chases per customer, **₹15,053** acquisition cost per activation.
- The steepest drop is **needs assessed → quote accepted (44%)**: price too high 414, competitor cheaper 207, quote too complex 206, too slow 179.
- About **1,950 leads are lost before a needs conversation** (unreachable 805, no time for a visit 531, invalid number 319, visit not scheduled 296).
- **Micro businesses lose money under field sales:** ₹20.0k CAC against a ₹2,470 median bundle and 22.7% churn.
- **Status chasing predicts churn:** 1 call → 5.9% churn and NPS 7.5, while 5 calls → 27.9% churn and NPS 6.0.
- **Compliance leak:** 68 of 368 activations (18%) broke a catalogue or GST rule, including 22 on cancelled or suspended GSTINs and 11 GSTIN-only products sold without a GSTIN.

## 2. Target customers and bundles (Q1)
Bundles are priced by the rules engine, include GST, and are the "Recommended" tier.

| Priority | Segment | Why | Channel | Starter bundle | ₹/month (12 → 24 mo) | Ready |
| --- | --- | --- | --- | --- | --- | --- |
| **1. Beachhead** | Professional offices (25% of base) | Best conversion (11.1%) and lowest CAC (₹10.7k); medium price sensitivity; needs fit a standard bundle | 100% self-serve | Fibre 300 + Cloud Email ×5 + Backup 1 TB + Endpoint ×5 (CA firm, 8 staff) | 4,712 → 4,198 | 5 days |
| **2. Volume** | Micro retail & services (55%) | Only viable without a visit: self-serve CAC ≈ website cost per lead | Self-serve + channel partner assist | Fibre 100 + Postpaid 299 + Cloud POS + WhatsApp Starter (with GSTIN) · no-GSTIN version: Fibre 100 + Cloud POS | 4,440 → 3,791 · 2,476 → 2,181 | 5 days |
| 3. Value | Small multi-site (15%) | ₹28k median bundle, 10.8% churn; one bill and central management are the pain | Advisor → field sales handoff (≥ 6 sites always) | Per-site Fibre 300 + Failover + SD-WAN + CCTV + POS, one bill (4 outlets) | 34,904 → 32,780 | 14 days |
| 4. Assisted | Small manufacturers (5%) | Highest conversion (12.8%), lowest churn (8.1%), complex needs | Advisor qualifies → field/partner | Leased Line 100 + Postpaid ×6 + Machine IoT ×5 + Endpoint (30 staff) | 49,357 → 48,384 | 30 days |

Pricing rule (one sentence for owners): **commit longer, pay less.** The minimum contract sits at the top of the catalogue range, and each extra month moves linearly to the bottom at +24 months.

## 3. Value
- **Owner:** one sitting, one price, one bill, one support number. The bundle is often cheaper than today's patchwork, and the advisor shows the difference against current spend.
- **Accel Business:** it takes the whole wallet (connectivity + cloud + security + CCTV), not one SIM. Lower CAC, faster activation, lower churn, and no compliance leak.
- **Field force and partners (Q4):** they get warm, ranked leads with an engine-priced recovery offer and a call brief in the owner's language, plus partner mode with attribution. Digital takes the contact-friction leads they lose today, and humans take multi-site, manufacturers and the "talk to an expert" requests.

## 4. Impact (impact simulator, conservative preset)
Each fix recovers a share of the exact drop reasons it addresses. Recovered leads then convert at today's rates for every later stage.

| Metric (Q5) | Today | Conservative | Expected | **Target** |
| --- | --- | --- | --- | --- |
| Lead-to-activation conversion | 7.4% | 15.6% | 21.8% | **≥ 12%** |
| Acquisition cost per activation | ₹15,053 | ₹5,499 | ₹3,172 | **≤ ₹6,000** |
| Days lead → activation | 17.6 | 8.6 | 8.6 | **≤ 9** |
| Status chases per customer | 3.0 | 2.0 | 1.5 | **≤ 1** |
| 6-month churn | 15.2% | 14.3% | 10.1% | **≤ 10%** |

On the same 5,000 leads a quarter, the conservative case gives 780 activations instead of 368, and the annualised bundle value of the cohort rises from ₹18.5 cr to ₹39.6 cr.

## 5. Rollout
1. **Pilot (months 0–3):** professional offices in 2 tier-1 cities (Pune, Bengaluru), self-serve web + WhatsApp, real GSTN lookup via a GSP, DigiLocker. Gate: ≥ 12% conversion and ≤ ₹6k CAC on pilot leads.
2. **Scale (months 3–9):** micro retail through 200 channel partners using partner mode; Hindi plus 4 regional languages (Bhashini); UPI AutoPay.
3. **Assist (months 6–12):** multi-site and manufacturers. The advisor qualifies the lead, field sales closes with the recovery brief, and installation slots come from the network inventory API.

## 6. Risks and mitigations
| Risk | Mitigation |
| --- | --- |
| LLM states a wrong price or product live | The engine decides; the fact guard blocks untraceable numbers and products; 16 QA scenarios run in CI |
| KYC fraud or forged documents | Prefer DigiLocker issuer-signed documents; GSTIN checksum and registry status; cross-document consistency; 90-day address proof |
| DPDP non-compliance | Consent receipt with notice hash, purpose limitation, no raw images stored, access log, one-tap withdraw (see `PRIVACY.md`) |
| Channel conflict with field and partners | Partner attribution kept on the order; human-only segments; recovery briefs make digital a lead source for the field |
| Fibre not feasible or slow installs | PIN coverage check at quote time with automatic AirFiber re-plan (2-day install) |
| Micro price sensitivity | No-GSTIN bundle from ₹2,181/month, a budget cap in the advisor, and a 24/36-month price shown up front |
