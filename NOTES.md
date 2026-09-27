# Project notes

Written 2026-09-27 while planning improvements. Tick items off as they are addressed.

## Confirmed issues

- [x] **Posted-card state does not carry over between runs.** Replaced 2026-09-27 with a stateless schedule: cards are ordered by a hash of their UUID and indexed by day number since 2025-01-01. No repeats for ~15 years, nothing stored. Cards added later carry an `added` date and are merged in after that day, so pool changes never resend old cards. The artifact steps were removed from the workflow.
- [ ] **Netlify publish directory mismatch.** `netlify.toml` sets `publish = "."` but the site lives in `public/`. Check whether the Netlify dashboard overrides this, then make the two agree.
- [x] **Downloader output does not match what the sender reads.** Fixed 2026-09-27: both scripts were rewritten around a new slim `metadata.json` (see README).
- [ ] **Orphaned file.** `card_00001.jpg` (604 KB) at the repo root is referenced nowhere.
- [ ] **Duplicate mobile CSS.** `public/styles.css` has two `@media (max-width: 768px)` blocks with conflicting timeline rules (grid-based, then float-based).
- [ ] **Unsubscribe copy is inconsistent.** The welcome email says to reply to unsubscribe; the daily email uses Resend's unsubscribe link.

## UX goal 1: stop sending the back of the card

Findings (2026-09-27):

- Every capture's `sortString` has four segments: `collection|series|card|side`. Side `0000000001` is the front, `0000000002` is the back.
- Verified visually on two pairs: "True Eagle." (imageID 1646639 front, 1646640 back) and "A is an ANGLER" (405573 front, 405574 back).
- Front and back are separate captures with separate UUIDs and consecutive imageIDs. NYPL does not link them explicitly, but the sort key pairs them reliably.
- Current metadata: 4,378 captures = 2,202 fronts + 2,176 backs. 26 cards have a front only.

Plan:

- [x] Filter to side 1 when choosing a card. (Done in `download_metadata.py`: the pool now holds one entry per card.)
- [x] Dedupe on the card, not the capture. (Moot now that nothing is tracked between runs; the pool has one entry per card.)
- [x] Show the back too. (Done 2026-09-27: the email shows front and back side by side, stacking on phones. Redesigned to match the site palette.)

## UX goal 2: expand the card pool

Findings (2026-09-27):

- Parent collection is **"Cigarette cards"**, UUID `b50ab6f0-c52b-012f-5986-58d385a7bc34`. The 46 hand-listed UUIDs in `download_metadata.py` are direct children of it.
- Parent totals: 1,217 series, 49,721 cards, 98,469 captures. We currently use 47 series (about 4% of the cards).
- `GET /api/v2/collections/{parent}` lists every series with title, `numItems`, and `orderInSequence`. That order equals segment 2 of each capture's `sortString`, so captures can be assigned to a series without per-series API calls.
- `GET /api/v2/items/{parent}?per_page=500` pages through all captures (197 pages, about 80 MB raw). `per_page=500` on the collections endpoint times out; use 100.
- Side-1 captures total 49,721, exactly one per card, confirming side 1 = front across the whole collection. 623 captures have side 3+ (folded "Histories of generals", embroidered Kensitas silks with covers).
- The NYPL API requires a token for every endpoint. The public site is JavaScript-rendered, so scraping is not an option.

Curation workflow (the user wants a manual pass, not all series are equally interesting):

- `curation/review.html` is a self-contained page listing all 1,217 series with three sample fronts each, card counts, search, filters, and checkboxes. The 47 series currently in use start pre-selected. Selection persists in the browser; "Export" produces `selected_series.json`.
- `curation/series.json` is the data behind it (uuid, title, counts, sample imageIDs, whether currently used). `curation/build_review.py` regenerates both from the API.

Plan:

- [x] Put `NYPL_TOKEN` in a local `.env` (already gitignored).
- [x] Find the parent collection and enumerate all series.
- [x] Manual pass in `curation/review.html`; saved as `curation/selected_series.json` (126 series, 5,439 cards, 51 without a back).
- [x] Rewrite the downloader. `download_metadata.py` now reads the selection and writes a 1.6 MB `metadata.json` of cards with front and back image IDs.
- [x] Keep the raw 80 MB capture dump out of git. (`curation/build_review.py --cache DIR` keeps it outside the repo.)
- [ ] Spot-check that chosen series are actually cards and that rights statements allow reuse.
