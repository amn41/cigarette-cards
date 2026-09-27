# Cigarette Card Club (A Daily Newsletter)

A simple newsletter that emails one vintage cigarette card a day, front and back. Emails go out through Resend; signups are handled by a small Netlify function.
You can sign up at [cigarettecard.club](https://cigarettecard.club/).

## Background

Cigarette cards were some of the world's first collectible cards, predating baseball cards and similar trading cards. Tobacco companies used them as both package stiffeners and marketing tools. The cards often came in themed sets and featured detailed illustrations and educational content on their backs, making them fascinating historical artifacts.

The New York Public Library has digitized over 100,000 cigarette cards, making them freely available through their Digital Collections API. Their "Cigarette cards" collection holds about 1,200 series and 50,000 cards; this newsletter sends from a hand-picked subset of those series.

## How it works

* `curation/review.html` is a page for choosing which NYPL series to send. Export your picks to `curation/selected_series.json`.
* `download_metadata.py` reads that selection, fetches every card in those series from the NYPL API, pairs each card's front with its back, and writes `metadata.json`.
* `broadcast_card.py` works out today's card, checks its images are reachable, and sends a Resend broadcast to the audience.
* `.github/workflows/daily_card.yml` runs the sender every day at 14:00 UTC.
* `public/` is the landing page and `netlify/functions/subscribe.js` adds new subscribers to the Resend audience.

## Setup

The GitHub Action needs these secrets:

* `RESEND_API_KEY`: Your Resend API key (e.g., `re_...`). **Required**.
* `RESEND_AUDIENCE_ID`: The ID of your Resend Audience to send the broadcast to. **Required**.
* `FROM_EMAIL`: The verified email address Resend will use in the "From" field (e.g., `"Your Name <sender@yourverifieddomain.com>"`). **Required**.
* `NYPL_TOKEN`: Your NYPL API token. Only needed to rebuild `metadata.json` or the curation page, not to send.

Nothing is tracked between sends. The pool is put in a fixed pseudo-random order (cards sorted by a hash of their UUID) and the number of days since 1 January 2025 picks the position, so every card goes out once before the sequence wraps, about fifteen years with the current pool. Cards added later are slotted into the order after the day they were added, so what has already gone out is never disturbed.

## Running locally

1. Put the variables above in a `.env` file.
2. `pip install -r requirements.txt`
3. Run the sender:
   ```bash
   MODE=preview python broadcast_card.py                   # writes preview_email.html for today's card, sends nothing
   MODE=preview DATE=2026-12-25 python broadcast_card.py   # preview another day's card
   TEST_TO=you@example.com python broadcast_card.py        # email today's card to one address only
   python broadcast_card.py                                # sends today's card to the audience
   ```

## Choosing which series to send

1. Serve the curation folder and open the review page:
   ```bash
   python -m http.server 8765 -d curation
   # then visit http://localhost:8765/review.html
   ```
   Each series shows three sample fronts and its card count. Tick the ones you want, then use **Export** to download `selected_series.json` and save it in `curation/`. **Import** loads a saved selection back in.
2. Rebuild the card pool (needs `NYPL_TOKEN`):
   ```bash
   python download_metadata.py
   ```
3. Commit the updated `curation/selected_series.json` and `metadata.json`.

To regenerate the review page itself, for example if NYPL adds series, run `python curation/build_review.py`. It downloads the full series list and every capture in the collection, which takes a few minutes.

### `metadata.json` format

```json
{
  "generated": "2026-09-27T14:02:11+00:00",
  "series": 126,
  "cards": [
    {
      "uuid": "5e66b3e9-1b32-d471-e040-e00a180654d7",
      "title": "True Eagle.",
      "series": "Indian chiefs",
      "front": "1646639",
      "back": "1646640",
      "link": "https://digitalcollections.nypl.org/items/5e66b3e9-1b32-d471-e040-e00a180654d7",
      "added": "2026-09-27"
    }
  ]
}
```

`front` and `back` are NYPL image IDs; `back` is `null` for the few cards digitized on one side only. Images are served from `https://images.nypl.org/index.php?id=<imageID>&t=w`. `added` is the date the card first entered the pool; `download_metadata.py` carries it over from the existing file, so keep the old `metadata.json` in place when rebuilding.

## Acknowledgments

* Card images and metadata are sourced from the [New York Public Library Digital Collections](https://digitalcollections.nypl.org/). Thank you, NYPL!
* Email delivery powered by [Resend](https://resend.com/).
