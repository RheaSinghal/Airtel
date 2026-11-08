# Execution plan

Each step is committed on its own. The tests have to keep passing: `cd backend && python -m pytest -q`.

- [x] **1. Problem → solution map**: all IDs. Files: `docs/PROBLEMS.md`. *Done when:* every case item has a row with a solution and status.
- [x] **2. Novelty research**: N1–N3. Files: `docs/NOVELTY.md`. *Done when:* the doc has 8–12 sourced projects, the patterns, and 2–4 ideas mapped to IDs.
- [x] **3. Design system + §20 Accel adaptation**: X1, P1. Files: `docs/DESIGN.md`. *Done when:* §20 covers brand, nav, phone-first, imagery, dependencies and the page checklist.
- [x] **4. N1 Fact guard**: D5, B1, Q2. Files: `backend/app/guard.py`, `backend/app/advisor/flow.py`, `backend/tests/test_guard.py`. *Done when:* `pytest tests/test_guard.py` passes, an LLM reply with an untraceable ₹ amount falls back to the template, and the violation count is exposed in `/api/backoffice/scenarios`.
- [x] **5. N2 Data passbook**: Q3, B3, E4, G3. Files: `backend/app/kyc/passbook.py`, `backend/app/main.py`, `backend/app/store.py`, tests. *Done when:* consent returns a receipt with a SHA-256 notice hash, `GET /api/orders/{id}/passbook` lists the receipt and access events, and withdraw is recorded.
- [x] **6. N3 Recovery playbook**: Q4, S2, S3, C7, D1. Files: `backend/app/recovery.py`, `backend/app/backoffice.py`, tests. *Done when:* every queue and call-list item has `recovery` (offer + engine price + brief) and the tests cover each drop reason family.
- [x] **7. D4 Leads audit**: D4. Files: `backend/app/backoffice.py`, tests. *Done when:* `insights.audit` reports the inactive-GSTIN activations (22), the GSTIN-only products sold without a GSTIN (11), and the tier (24), min-employee (8) and dependency (9) violations.
- [x] **8. Submission docs**: E1, E2, E3, E4, Q1, Q5. Files: `docs/ARCHITECTURE.md`, `docs/BUSINESS_CASE.md`, `docs/PRIVACY.md`, `docs/DEMO_SCRIPT.md`. *Done when:* each exists, and its numbers match `/api/backoffice/insights` and `/api/impact`.
- [x] **9. Restyle every page to DESIGN.md + novelty UI**: X1, P1, N2, N3, D4. Files: `frontend/src/app/**`, `frontend/src/components/**`, `globals.css`, `layout.tsx`. *Done when:* `npm run build` passes and every page in the DESIGN.md §20 checklist has been checked at 360 px and desktop.
- [ ] **10. Coverage re-check**: all IDs. Files: `docs/PROBLEMS.md`. *Done when:* every row is done except E1 (the video recording is manual).
- [ ] **11. Round 1 deck**: R1 and all IDs. Files: `deck/`, `Kernel_TIET.pptx`, `Kernel_TIET.pdf`. *Done when:* there are 7 slides on the official template, exported through PowerPoint to PDF, and two render-and-critique passes are done.
- [ ] **12. Code walkthrough**. Files: `docs/CODE_WALKTHROUGH.md`. *Done when:* a new reviewer can run the app and follow each journey step to code.
