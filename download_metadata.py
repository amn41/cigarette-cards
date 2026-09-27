"""Build metadata.json from the NYPL series chosen in curation/selected_series.json.

For each selected series this pages through its captures, pairs every card's
front (side 1 of the sort key) with its back (side 2), and writes a slim list
of cards that broadcast_card.py picks from. Each card records the date it
first entered the pool ("added"); dates are carried over from the existing
output file so the sending order stays stable when the pool changes.

Usage:
    python download_metadata.py [--selection curation/selected_series.json] [--output metadata.json]

Requires NYPL_TOKEN in the environment or a .env file.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

API = "https://api.repo.nypl.org/api/v2"
FRONT, BACK = "0000000001", "0000000002"


def fetch_captures(session, series_uuid, per_page=500):
    """Yield every capture in a series, following pagination with retries."""
    page = 1
    while True:
        for attempt in range(5):
            try:
                r = session.get(f"{API}/items/{series_uuid}",
                                params={"page": page, "per_page": per_page}, timeout=120)
                r.raise_for_status()
                break
            except requests.RequestException as e:
                wait = 3 * (attempt + 1)
                print(f"  page {page} failed ({e}); retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
        else:
            raise RuntimeError(f"gave up fetching series {series_uuid}, page {page}")

        j = r.json()["nyplAPI"]
        caps = j["response"].get("capture") or []
        if isinstance(caps, dict):
            caps = [caps]
        yield from caps
        if not caps or page >= int(j["request"].get("totalPages", 1)):
            return
        page += 1
        time.sleep(0.5)


def cards_for_series(captures, series_title):
    """Group captures by card (sort key minus the side) and pair front with back."""
    by_card = {}
    for c in captures:
        seg = (c.get("sortString") or "").split("|")
        if len(seg) != 4 or not c.get("imageID"):
            continue
        by_card.setdefault(tuple(seg[:3]), {})[seg[3]] = c

    cards = []
    for key in sorted(by_card):
        sides = by_card[key]
        front = sides.get(FRONT)
        if not front:
            continue
        back = sides.get(BACK)
        cards.append({
            "uuid": front["uuid"],
            "title": (front.get("title") or "Untitled card").strip(),
            "series": series_title,
            "front": front["imageID"],
            "back": back["imageID"] if back else None,
            "link": f"https://digitalcollections.nypl.org/items/{front['uuid']}",
        })
    return cards


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selection", default="curation/selected_series.json",
                    help="JSON list of selected series (exported from curation/review.html)")
    ap.add_argument("--output", default="metadata.json")
    args = ap.parse_args()

    load_dotenv()
    token = os.getenv("NYPL_TOKEN")
    if not token:
        sys.exit("NYPL_TOKEN is not set. Put it in .env or the environment.")

    selection = json.loads(Path(args.selection).read_text())
    session = requests.Session()
    session.headers["Authorization"] = f'Token token="{token}"'

    all_cards, seen = [], set()
    for i, s in enumerate(selection, 1):
        uuid = s["uuid"] if isinstance(s, dict) else s
        title = s.get("title", uuid) if isinstance(s, dict) else uuid
        print(f"[{i}/{len(selection)}] {title}", flush=True)
        cards = [c for c in cards_for_series(fetch_captures(session, uuid), title) if c["uuid"] not in seen]
        seen.update(c["uuid"] for c in cards)
        print(f"    {len(cards)} cards, {sum(1 for c in cards if c['back'])} with backs", flush=True)
        all_cards.extend(cards)
        time.sleep(0.5)

    previous = {}
    if Path(args.output).exists():
        try:
            previous = {c["uuid"]: c.get("added") for c in json.loads(Path(args.output).read_text())["cards"]}
        except (ValueError, KeyError, TypeError):
            print(f"Could not read existing {args.output}; treating every card as new", file=sys.stderr)
    today = datetime.now(timezone.utc).date().isoformat()
    for c in all_cards:
        c["added"] = previous.get(c["uuid"]) or today
    print(f"{sum(1 for c in all_cards if c['added'] == today)} cards new today")

    out = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "series": len(selection),
        "cards": all_cards,
    }
    Path(args.output).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(all_cards)} cards from {len(selection)} series to {args.output}")


if __name__ == "__main__":
    main()
