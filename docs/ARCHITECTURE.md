# Solution architecture

**Principle: the LLM talks, deterministic code decides.** Eligibility, prices, KYC verdicts and routing all come from code over the case data. The LLM, which is optional and set by provider-neutral environment variables, extracts facts from free text, rephrases into the owner's language and writes the "why". Everything it writes passes the fact guard.

```mermaid
flowchart LR
  subgraph Owner["Owner's phone"]
    PWA["Next.js PWA<br/>advisor · quote · KYC · tracker · account"]
    WA["WhatsApp<br/>(Cloud API)"]
  end
  subgraph Partner["Field sales / channel partner"]
    BO["Back-office<br/>queue · call list · insights · QA"]
    PM["Partner mode<br/>/advisor?partner=CODE"]
  end

  PWA -->|REST /api| API
  PM --> API
  WA -->|webhook| API
  BO --> API

  subgraph API["FastAPI backend"]
    ADV["Advisor dialogue<br/>slot filling, NLU (EN/HI)"]
    GUARD["N1 Fact guard"]
    ENG["Rules & pricing engine<br/>eligibility · bundler · pricing · why-not"]
    ORD["Orders & tracker<br/>stages · install dates · slots"]
    KYC["Smart KYC<br/>OCR · checksum repair · validators"]
    DL["DigiLocker + e-Sign (mock)"]
    PB["N2 Data passbook<br/>consent receipt · access log"]
    BOS["Back-office services<br/>propensity · routing · N3 recovery · D4 audit"]
    IMP["Impact simulator"]
    FEAS["Coverage by PIN"]
  end

  ADV --> ENG
  ADV -. optional .-> LLM["LLM (OpenAI-compatible)<br/>extract · phrase · explain"]
  LLM --> GUARD --> ADV
  ADV --> FEAS
  ORD --> ENG
  KYC --> REG["Mock GSTIN & Udyam registries"]
  DL --> REG
  KYC -. optional gap-fill .-> VIS["Vision model"]
  KYC --> PB
  BOS --> ENG
  ENG --> CAT[("product_catalogue.csv")]
  BOS --> LEADS[("smb_leads.csv")]
  IMP --> LEADS
  API --> DB[("SQLite: sessions, orders,<br/>extracted fields, masked events")]
```

## Request flow per journey step

| Step | Call | What happens |
| --- | --- | --- |
| Advisor | `POST /api/advisor/sessions/{id}/messages` | NLU (+ LLM) extracts facts → code picks the next question → once enough is known, `build_offer` returns 3 tiers → LLM explanation vetted by the fact guard |
| Quote | `POST /api/quote` | Toggled items re-priced by `pricing.quote` (one GST-inclusive monthly price) |
| Order | `POST /api/orders` | Bundle re-validated by `rules.check_bundle`; tracker plan from `typical_install_days` |
| KYC | `POST /api/orders/{id}/consent` → `/documents/{slot}` → `/kyc/verify` | Consent receipt issued → OCR in memory (image discarded) → GSTIN checksum, registry status, cross-document, 90-day checks → GST-only products blocked on a bad GSTIN |
| Tracker | `GET /api/orders/{id}`, `/passbook` | Stage timeline, planned dates, proactive updates, data passbook |
| Back-office | `GET /api/backoffice/queue`, `/call-list`, `/insights` | Ranked by propensity (AUC 0.73), routed, each with an engine-priced recovery offer; leads audit |

## Production path (not built)
SQLite becomes Postgres with row-level security, and documents stay in memory only, as they do now. The mocks are replaced by GSTN/Udyam APIs through a GSP, real DigiLocker Requester APIs, Aadhaar e-Sign through an ESP, Bhashini ASR/TTS for more languages, UPI AutoPay mandates, and the network inventory API in place of the PIN mock.
