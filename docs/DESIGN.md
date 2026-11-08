# Design system: Accel Business · Udyam Digital

Design language adapted from the editorial style of [bharatdigital.org/fellowship](https://bharatdigital.org/fellowship): warm paper backgrounds, a large serif display face over a quiet sans, generous whitespace, numbered editorial lists, documentary-style imagery, paired calls to action and a four-column footer. We take only the language, never their brand assets (see §20).

## 1. Principles
1. **Calm, editorial, trustworthy.** It reads like a well-set newspaper, not a telecom promo.
2. **One task per screen.** The owner always knows the next step.
3. **Numbers are the hero.** Prices, dates and statuses are set large, in tabular figures.
4. **Plain words.** No product codes in the UI. Every term an owner might not know gets a one-line explanation.

## 2. Colour tokens
| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--background` (cream) | `#F6F1E7` | `#171512` | Page |
| `--surface` (paper) | `#FFFDF8` | `#211E1A` | Cards, inputs |
| `--surface-2` (sand) | `#EDE6D6` | `#2B2722` | Chips, quiet fills |
| `--foreground` (charcoal) | `#1F1D1A` | `#F3EDE2` | Text, primary buttons |
| `--muted` | `#6B655B` | `#ADA597` | Secondary text |
| `--border` | `#E2D9C6` | `#3A352E` | Hairlines |
| `--brand` (saffron) | `#C2410C` (text-safe) | `#F0A35E` | Links, focus, key numbers |
| `--saffron` | `#F29A4A` | `#F0A35E` | Accent fills, highlights, bars |
| `--brand-soft` | `#FBE7D3` | `#3A2716` | Accent backgrounds |
| `--ok` / `--ok-soft` | `#2F6B3F` / `#E3EFE3` | `#7FCB92` / `#16301E` | Success |
| `--warn` / `--warn-soft` | `#8A5A00` / `#FBF0D9` | `#F2C46B` / `#33280F` | Attention |
| `--bad` / `--bad-soft` | `#A8322A` / `#F7E1DE` | `#FF8A80` / `#3A1714` | Errors |

Charcoal carries the weight and saffron stays an accent (under ~10% of any screen). Red is reserved for errors, which also keeps us clear of the Airtel/SYNC template red in the deck.

## 3. Typography
- **Display:** Instrument Serif 400 (regular and italic). Used for headings and large numbers on the landing page and deck.
- **Body / UI:** DM Sans 400/500/600/700.
- **Devanagari and other scripts:** Noto Sans Devanagari as fallback after DM Sans.
- **Scale:** 12 / 14 / 16 / 18 / 22 / 28 / 40 / 56 / 72. Body text 16, line-height 1.55. Display line-height 1.05, letter-spacing −0.01em.
- **Italic accent:** one italic word in a display heading for emphasis ("in *one sitting*").
- Figures: `font-variant-numeric: tabular-nums` for prices and dates.

## 4. Layout
- Content max width 1120 px (landing), 720 px (journey screens). Side gutter 16 px on phones, 24 px at ≥ 640 px.
- 8 px spacing grid; section spacing 64–96 px on the landing page, 24–32 px in-app.
- 12-column grid at ≥ 1024 px, single column below 640 px.

## 5. Header / navigation
Sticky, cream at 92% with blur, hairline bottom border, height 56 px. Wordmark on the left, then nav links in DM Sans 500 14 px, language select and primary CTA on the right. On phones the links collapse into a "Menu" sheet.

## 6. Buttons
- **Primary:** charcoal fill, cream text, pill (`radius 999px`), 48 px tall on phones and 44 px on desktop, padding 0 24 px, DM Sans 600.
- **Secondary:** transparent, 1 px charcoal border, pill.
- **Accent:** saffron fill, charcoal text. Use once per screen at most, for the money moment (Pay / Place order).
- **Text link:** saffron (`--brand`) underline offset 3 px.
- Pressed: scale 0.98. Focus: 2 px saffron outline, 2 px offset.

## 7. Cards
Paper surface, 1 px border, radius 20 px, padding 20–24 px, no drop shadow (or `0 1px 0` hairline only). Hover on desktop: border goes charcoal.

## 8. Numbered lists
Editorial "01–06" lists: the number is in Instrument Serif at 40 px in saffron, and the title and body sit beside it. Used for "How it works" and back-office steps.

## 9. Forms
Inputs 48 px, paper fill, 1 px border, radius 12 px, label above in 14 px 500. Error text in `--bad` below the field. Chips: pill, sand fill, charcoal text when selected.

## 10. Chat
Assistant bubbles on paper with a border, user bubbles in charcoal with cream text, radius 20 px with a 6 px corner on the speaker side. Quick-reply chips sit under the last message.

## 11. Status
Status badges are pills with soft fill and strong text (`ok`, `warn`, `bad`, `brand`). Timelines use a 2 px line; completed steps get a charcoal dot, the current step a saffron ring, and future steps a hollow dot.

## 12. Data display
Big number in Instrument Serif 40–56 px, label in 12 px uppercase DM Sans 600 with 0.08em tracking. Bars use saffron for the highlight and sand/charcoal-30% for the rest.

## 13. Imagery
Documentary photography of real small businesses (licensed), or compositions made from type and shapes. No stock-smile portraits, no AI-generated people.

## 14. Iconography
1.75 px stroke line icons, 20–24 px, current colour.

## 15. Motion
Fade and rise (8 px) on enter at 200–320 ms with `cubic-bezier(.2,.7,.2,1)`. Stagger list items by 40 ms. No parallax. Respect `prefers-reduced-motion: reduce` by disabling transforms and keeping opacity only.

## 16. Footer
Charcoal block with cream text, four columns (Explore · For business · Partners · Help), the wordmark, a one-line note that the data is synthetic, and a "©2026" line.

## 17. Accessibility
Text contrast is AA at minimum. Touch targets are at least 44 × 44 px. Every icon button has a label. Language is set on `<html lang>`. Focus is always visible.

## 18. Voice and tone
Talk like a helpful shopkeeper's nephew: short sentences, rupees not "INR", "per month" not "MRC".

## 19. Dark mode
Swap to the dark token column. Charcoal buttons invert to cream with charcoal text.

## 20. Accel adaptation

### Brand
We keep the case's fictional **Accel Business** brand: a type-only wordmark, "Accel" in Instrument Serif and "Business" in DM Sans 600, with a small saffron dot. Only the design language comes from bharatdigital.org. We don't copy its logo, wordmark, copy, images or partner marks.

### Navigation
The reference site's links (Home, Fellowship, About, Get Involved) become this app's routes:

| Label | Route |
| --- | --- |
| Advisor | `/advisor` |
| Quote | `/quote` |
| Track order | `/order/[id]` (lookup on the landing page) |
| Account | `/account/[id]` |
| Partners / Back-office | `/backoffice` |
| Impact | `/impact` |

Journey screens show a compact header (back arrow, title, language) so the task stays on screen. The full nav appears on the landing page and on desktop.

### Phone first
Owners use phones. Every journey screen (advisor chat, quote, KYC, tracker) is designed for **360 px width first**, with 48 px touch targets, a sticky bottom action bar where there is a primary action, and no horizontal scroll. Editorial display sizes (56–72 px) are for the landing page only. In-app screens use 22–28 px Instrument Serif headings.

### Imagery
Only licensable images (for example Unsplash, credited in the footer) or type-and-shape compositions. The prototype uses type and shape compositions only, so no credits are needed yet.

### Dependencies
Fonts load through `next/font/google` (Instrument Serif, DM Sans, Noto Sans Devanagari). There is no Motion library because CSS transitions cover every case, and `prefers-reduced-motion` is respected in `globals.css`.

### Page checklist
Tick a page only after it has been opened at 360 px and at desktop width and matches this document.

- [x] `/` landing
- [x] `/advisor`
- [x] `/quote`
- [x] `/order/[id]/kyc`
- [x] `/order/[id]` tracker
- [x] `/account/[id]`
- [x] `/whatsapp`
- [x] `/backoffice`
- [x] `/impact`
