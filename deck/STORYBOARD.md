# Round 1 deck: Kernel_TIET

## World
**"The shop counter ledger."** A small-business owner's day is counted in rupees, days and phone calls. The deck reads like a clean ledger laid on the official SYNC page: cream ledger cards, charcoal ink, one saffron highlight per slide, and numbers set large in a serif. It looks like one product with the app (`docs/DESIGN.md`).

## Frame (mandatory template)
Built on `Submission Template_Sync.pptx` (16:9, 10 × 5.625 in).
- **Slide 1** keeps the SYNC cover image. Title, team and campus sit in the dark lower-left, clear of the globe.
- **Slides 2–7** sit on the white content background. Safe area: x 0.45–9.55 in, y 0.80–5.10 in. This clears the Airtel and SYNC logos (top 0.75 in), the Unstop mark (bottom-right, from y 5.15 in) and the red bar.
- The template red appears only in the template art. Saffron is the deck accent and charcoal carries the weight, so the two never touch.

## Design system
| Token | Hex | Use |
| --- | --- | --- |
| Charcoal | `1F1D1A` | Titles, body, dark cards |
| Cream | `F6F1E7` | Ledger cards |
| Sand | `EDE6D6` | Quiet fills, bars |
| Saffron | `F29A4A` | One highlight per slide (key bar, key number) |
| Deep saffron | `C2410C` | Accent text on light backgrounds |
| Muted | `6B655B` | Captions, sources |
| Green | `2F6B3F` | "After" numbers |

Type: Georgia for headings and big numbers (the closest installed stand-in for Instrument Serif), Segoe UI for body (for DM Sans). Titles are 24 pt, numbers 26–40 pt, body 10.5–12 pt, captions 8–9 pt. This is a pre-read deck for judges, so it runs denser than a live deck.

Motif: **ledger cards**, rounded cream rectangles, each topped by a small serif number or eyebrow label. No accent stripes or underlines.

## Storyboard (7 slides, each traced to PROBLEMS.md)
| # | Message (title) | Visual | IDs |
| --- | --- | --- | --- |
| 1 | Udyam Digital: your business online, in one sitting | SYNC cover, title block | — |
| 2 | 7.4% of leads activate; the funnel leaks at the quote and at the door | Funnel bars with the 44% quote step in saffron · 4 stat cards · today's journey strip | C1–C8, D1–D3, D4 |
| 3 | Lead with professional offices; serve micro shops without a visit | 4 segment ledger cards: why, channel, engine-priced bundle, ₹/month, contract | Q1, D2, D3 |
| 4 | One sitting on a phone: advise → price → verify → track | 4 real prototype screenshots in phone frames + one fact under each | Q2, Q3, B1–B4, S1, C2–C5 |
| 5 | The LLM talks, code decides, and the field force gets a better brief | 3 novelty cards (N1–N3, credited) + field/partner routing strip + audit figure | NOVELTY, Q4, S2, S3, D4, D5 |
| 6 | Architecture and privacy by design | Shape-built flow diagram + DPDP column | E2, E4, Q3 |
| 7 | Conservatively, activations double and cost per activation falls 64% | Metrics table today → simulated → target · 3-phase rollout · risks | Q5, E3 |

## Motion plan
- **Transition:** fade (medium) on every slide.
- **Build:** each slide auto-plays a staggered fade-in after it appears, with no clicks needed: title → main visual → cards left to right (every 120 ms) → takeaway line. About 1.2 s per slide, so a live presenter is never waiting.
- **Cover:** the title fades in, then team and campus.
- The exported PDF shows the final state.
