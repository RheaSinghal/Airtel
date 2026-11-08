# Privacy and security note (DPDP Act 2023)

**Role.** Accel Business acts as the *data fiduciary* for KYC data collected to activate telecom services. Every choice below maps to a DPDP principle.

**1. Consent that can be proven (s.6).** Before any upload, the owner sees a notice in their language listing the purpose, the exact documents, how long they are kept, their rights, and who never sees them. The notice can be read aloud. Accepting issues a **consent receipt**: receipt ID, notice version, SHA-256 of the exact notice text, purposes, data items and retention date (`kyc/passbook.py`). If the wording changes later, the hash no longer matches.

**2. Purpose limitation.** KYC data is used only to verify business identity and address (`purposes: ["kyc_verification"]`). It is never shared with sales partners or used for marketing. The partner sees the lead and the offer, never the documents.

**3. Data minimisation.**
- The GSTIN lookup pre-fills legal name and address, so less needs uploading.
- DigiLocker replaces photos with issuer-signed records.
- No-GSTIN owners are asked only for what their products need.
- **Raw images are never stored.** They are read in memory and dropped when the request returns. Only the extracted fields are kept.

**4. Masking everywhere.** GSTIN, Udyam, ID and consumer numbers are masked in every API response, in the UI and in the audit log (`mask_gstin`, `mask_udyam`, `mask_id`). Audit events take masked values only.

**5. Transparency: data passbook.** On the order tracker, the owner can see their receipt and an **access log** of every time the system or staff touched their data: document read, registry check, DigiLocker fetch, e-Sign, and back-office views of KYC issues.

**6. Retention and erasure (s.8(7), s.12).** Verified fields are kept for the configured retention period after activation, or as telecom licence rules require. **Withdrawing consent** (one tap) deletes the extracted fields and the KYC result immediately and leaves an audit entry. Before activation, it also cancels the order.

**7. Accuracy (s.8(3)).** Checksummed GSTINs with OCR repair, registry status checks, cross-document name, PIN and signatory checks, and a 90-day address proof rule. A blurry document is re-requested, never guessed by a model.

**8. Security safeguards (s.8(5)).**
- Prototype: SQLite with no images; secrets only in `.env`; CORS restricted.
- Production plan: Postgres with encryption at rest and row-level security, TLS everywhere, role-based back-office access (partners see only their own leads), and KMS-managed keys.
- The LLM receives business facts, not identity documents, unless the optional vision gap-fill is turned on. It is never called on a blurred image.

**9. AI safety.** The LLM never sets prices or eligibility. The fact guard rejects any LLM sentence whose rupee amounts or products aren't in the engine's output, and logs the event.

**10. Breach readiness (s.8(6)).** The masked event log gives a ready timeline of who accessed what, for notifying the Data Protection Board and affected owners.
