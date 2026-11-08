# Novelty: what recent winners did, and what we borrow

Research done on 2026-11-08 through web search. I looked for 2025–2026 winning projects close to this case: MSME digitisation, GenAI advisors and agents, instant KYC, vernacular and voice-first services, and India Stack consent flows. Few corporate hackathons (Flipkart GRiD, PhonePe, Razorpay, Airtel, Jio) publish project-level winner write-ups, so the table leans on events that do. One 2024 entry (Sahamati) is included because it is the closest consent-flow precedent; it is marked.

## Projects

| # | Project | Event | Year | Link | Core idea | What judges rewarded |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **MEGHA** (Meghalaya E-Governance Human-centred Assistance) | Harvard Kennedy School AI for Good Hackathon, **1st prize** | 2025 | [Free Press Journal](https://www.freepressjournal.in/india/ai-solution-for-india-wins-top-spot-at-harvards-hackathon) | Toll-free, voice-first assistant for government schemes on any basic phone; answers grounded only in verified official documents | Reach to low-literacy users; answers that can't drift from official sources ("solving something real") |
| 2 | **ArtisanGully** | Google Cloud Gen AI Exchange Hackathon, track winner | 2025 | [Hack2skill](https://blog.hack2skill.com/gen-ai-exchange-hackathon-finale) | Artisan sends a photo or voice note; agents turn it into a listing, styled images and a video ad | Removes the "digital literacy" barrier for small sellers; one input, many outputs |
| 3 | **Legal SahAI** | Gen AI Exchange Hackathon, track winner | 2025 | [Hack2skill](https://blog.hack2skill.com/gen-ai-exchange-hackathon-finale) | RAG explanation of legal documents plus an AI form-filling assistant and a lawyer–client portal | Makes a dense document readable to a layperson, end to end |
| 4 | **May The Agents Be With You** (cement operations) | Gen AI Exchange Hackathon, track winner | 2025 | [Hack2skill](https://blog.hack2skill.com/gen-ai-exchange-hackathon-finale) | Autonomous agents optimise plant operations; humans approve the key decisions | Real industrial value with a human in control |
| 5 | **PitchLense** | Gen AI Exchange Hackathon, track winner | 2025 | [Hack2skill](https://blog.hack2skill.com/gen-ai-exchange-hackathon-finale) | Parses founder documents into risk reports, scores and a copilot for the analyst | Automates most of an analyst's preparation, then hands over to a human |
| 6 | **Skippers** (test-case generation) | Gen AI Exchange Hackathon, track winner | 2025 | [Hack2skill](https://blog.hack2skill.com/gen-ai-exchange-hackathon-finale) | Requirement documents become traceable, GDPR-safe test cases in Jira | Traceability and privacy built in, not bolted on |
| 7 | **MoneyMitra** | MumbaiHacks 2025, fintech track winner | 2025 | [Tribune](https://www.tribuneindia.com/news/business/mumbaihacks-2025-crowns-indias-next-gen-ai-innovators-with-inr-1-crore-cash-and-rewards-marking-the-worlds-largest-agentic-ai-hackathon) | Personal finance agent: OCR and SMS transaction parsing, alerts, multilingual literacy modules | Works on messy real inputs (receipts, SMS) in the user's language |
| 8 | **Padhai Check** | MumbaiHacks 2025, misinformation track winner | 2025 | [Tribune](https://www.tribuneindia.com/news/business/mumbaihacks-2025-crowns-indias-next-gen-ai-innovators-with-inr-1-crore-cash-and-rewards-marking-the-worlds-largest-agentic-ai-hackathon) | Agent checks exam claims against official sources and replies in Hinglish | Every claim checked against a source of truth before it reaches the user |
| 9 | **AI chatbot for the MSME One Portal** | APIS MSME Digital Hackathon (Andhra Pradesh) | 2025 | [Viscan](https://viscan.in/apis-announces-winners-of-msme-digital-hackathon-2025/) | Conversational front door to a state MSME services portal | MSME self-service without a field officer |
| 10 | **DreamOps** | Devfolio Warpspeed, **grand prize** | 2025 | [Devfolio](https://devfolio.co/blog/warpspeed-2025-recap/) | AI agent handles on-call incidents, escalating to humans only when needed | Agent does the routine 80%, humans get a prepared handover |
| 11 | **PragyanAI** | Devfolio Warpspeed, 1st runner-up | 2025 | [Devfolio](https://devfolio.co/blog/warpspeed-2025-recap/) | Multilingual learning companion | Vernacular-first experience |
| 12 | **Multilingual GenAI voice bot for AA consent** *(2024, closest consent precedent)* | Sahamati Account Aggregator BuildAAthon, listed project | 2024 | [Sahamati](https://sahamati.org.in/buildathon-2024-project-list/) | Collects Account Aggregator consent over a phone call, explaining each item and answering questions in the user's language | Consent that people actually understand, not a checkbox |

## Recurring patterns

1. **Grounding beats fluency.** MEGHA and Padhai Check won because the model can't say what the source of truth doesn't support. Judges reward trustworthy answers, not clever ones.
2. **Meet users in their channel and language.** Voice on a basic phone (MEGHA), voice notes (ArtisanGully), Hinglish (Padhai Check), phone-call consent (Sahamati).
3. **The agent does the routine work; a human gets a ready-made handover.** DreamOps, PitchLense and the cement agents all end in a prepared brief and a human decision.
4. **Privacy and traceability as features.** Skippers (GDPR-safe, traceable) and the Sahamati consent bot make compliance something the user can see.
5. **Messy real inputs** (photos, SMS, scans) turned into structured data. We already do this with KYC OCR, the GSTIN checksum repair and DigiLocker.

## What the repo already had

We already had a rules-decided advisor, "why not X?" traces, voice in and out, 10 languages, WhatsApp, a DigiLocker/e-Sign mock, a propensity-ranked queue and an impact simulator. Patterns 2 and 5 were covered. The gaps were in patterns 1, 3 and 4:

- The LLM's text was prompted to stay on facts but **never checked**.
- Consent could be given and withdrawn, but the owner got **no receipt** and **couldn't see who used their data**.
- The back-office said **who** should call a lead, but **not what to offer**.

## Ideas we add (adapted, not copied)

### N1: Fact guard on every LLM sentence
*Inspired by MEGHA and Padhai Check (answers checked against a source of truth).*

- **What:** Before any LLM-written explanation, answer or translation reaches the owner, a deterministic checker pulls out every rupee amount, product name and product ID. Each one must appear in the facts the engine produced for that turn. If anything can't be traced, the reply is replaced by the engine's own template, and the event is counted for QA.
- **Strengthens:** D5 (never a wrong price live), B1, Q2, the core principle "the LLM talks, code decides".
- **Why new here:** Before this, the prompts only *asked* the model to keep to the facts. Now the code *proves* it does, on every turn and in every language, and logs a violation count the QA tab can show.
- **Effort:** S (one module, hooks in `advisor/flow.py`, unit tests).

### N2: DPDP data passbook (consent receipt, access log, listen-aloud consent)
*Inspired by the Sahamati multilingual consent bot (consent people understand) and Skippers (privacy you can see).*

- **What:** Giving consent issues a **receipt**: consent ID, purposes, data items, retention period, timestamp and a SHA-256 hash of the exact notice shown. Every read or write of KYC data by the system or back-office staff is appended to an **access log**. The owner can see both on the tracker, alongside a one-tap withdraw. The consent notice can be **read aloud** in the owner's language.
- **Strengthens:** Q3, B3, E4, G3, Q2.
- **Why new here:** The repo had consent and withdraw but nothing the owner keeps, and no visibility into use. DPDP s.6 consent has to be "free, specific, informed"; a receipt with the notice hash and a log is evidence of that.
- **Effort:** S–M (store table, two endpoints, a tracker card, tests).

### N3: Recovery playbook for field sales and partners
*Inspired by DreamOps and PitchLense (agent prepares, human closes) and the cement agents (human approves).*

- **What:** Every lead in the back-office queue, and every historical drop on the call-back list, gets a **recovery offer** computed by the rules engine for its drop reason:
  - "price too high" or "competitor cheaper": the 24- or 36-month price, or the Essential tier under their spend
  - "quote too complex": a three-line plain summary
  - KYC missing documents: a DigiLocker link
  - no fibre: AirFiber
  - "no time for a visit": a self-serve link with the partner code

  It also gets a **call brief** in the owner's preferred language. The partner keeps attribution.
- **Strengthens:** Q4 (digital arms the field force instead of replacing it), S2, S3, C7, D1.
- **Why new here:** Routing said *who*. Now the human gets *what to say and what to offer*, and the offer is still engine-priced, so a rep can't promise a price the engine wouldn't give.
- **Effort:** M (module, two endpoint fields, back-office UI column, tests).

### Considered and skipped
- **Photo of current telecom bill → savings** (after MoneyMitra and ArtisanGully). It's strong, but the data pack has no telecom bills to test against, and a demo on invented bills would weaken the evidence. It's on the roadmap instead.
- **Phone-call voice agent (IVR).** Impressive, but it repeats the WhatsApp and browser-voice channels we already have, so it adds show without adding to the case.
