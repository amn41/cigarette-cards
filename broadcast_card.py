"""Send today's cigarette card to the Resend audience.

Picks today's card from metadata.json, checks that its images are reachable,
and sends a broadcast showing the front and back of the card.

Which card is "today's" needs no stored state. The pool is put in a fixed
pseudo-random order (cards sorted by a hash of their UUID) and the day number
since a fixed epoch indexes into it, so every card goes out once before any
repeats. Cards added to the pool later (their "added" date, set by
download_metadata.py) are merged into the part of the order after the day they
were added, so cards already sent keep their place and are not repeated.

Environment (via .env or the shell):
    RESEND_API_KEY, RESEND_AUDIENCE_ID, FROM_EMAIL   required to send
    METADATA_PATH   default metadata.json
    MODE            "preview" writes preview_email.html and sends nothing
    DATE            YYYY-MM-DD to pick another day's card (default: today, UTC)
    TEST_TO         an email address: send today's card there as an ordinary
                    email instead of broadcasting to the audience
"""
import hashlib
import html
import json
import os
import random
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests
import resend
from dotenv import load_dotenv

SITE_URL = "https://cigarettecard.club"
EPOCH = date(2025, 1, 1)      # day 0 of the sending sequence
ORDER_SEED = "cigarettecard"  # change to reshuffle the whole sequence


def image_url(image_id):
    """Direct NYPL image URL, 'w' size (up to 760px wide)."""
    return f"https://images.nypl.org/index.php?id={image_id}&t=w"


# --- Card selection ---------------------------------------------------------

def load_json(path, default):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return default


def load_cards(metadata_path):
    data = load_json(metadata_path, None)
    if not data or "cards" not in data:
        raise SystemExit(f"{metadata_path} is missing or not in the expected format; run download_metadata.py")
    return data["cards"]


def order_key(card):
    return hashlib.sha256(f"{ORDER_SEED}:{card['uuid']}".encode()).hexdigest()


def card_order(cards):
    """The pool in sending order: a fixed shuffle, independent of file order.

    Cards are grouped by the date they were added. The first group is simply
    sorted by hash. Each later group is merged (again by hash) into the positions
    from its added-day onwards, leaving earlier positions, and so cards already
    sent, untouched.
    """
    groups = {}
    for c in cards:
        groups.setdefault(c.get("added") or "", []).append(c)
    order = []
    for added, group in sorted(groups.items()):
        if not order:
            order = sorted(group, key=order_key)
            continue
        cut = (date.fromisoformat(added) - EPOCH).days % len(order)
        order = order[:cut] + sorted(order[cut:] + group, key=order_key)
    return order


def card_for_day(cards, day):
    """The card scheduled for a date: day number since EPOCH, wrapping around the pool."""
    ordered = card_order(cards)
    return ordered[(day - EPOCH).days % len(ordered)]


def fallback_card(cards, exclude):
    """A random stand-in when the scheduled card's images are unavailable."""
    available = [c for c in cards if c["uuid"] not in exclude]
    if not available:
        raise RuntimeError("No cards left to choose from")
    return random.choice(available)


def resolve_day():
    override = os.getenv("DATE")
    return date.fromisoformat(override) if override else datetime.now(timezone.utc).date()


def verify_image(url):
    """Raise if the URL does not serve an image."""
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    if not r.headers.get("Content-Type", "").startswith("image/"):
        raise RuntimeError(f"not an image ({r.headers.get('Content-Type')}): {url}")


# --- Email ------------------------------------------------------------------

SANS = "Helvetica, Arial, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"


def side_block(src, alt):
    """One side of the card. Sits beside its partner when there is room, stacks when there is not."""
    return (
        f'<div style="display:inline-block;width:100%;max-width:270px;vertical-align:top;">'
        f'<div style="padding:0 15px 20px;text-align:center;">'
        f'<img src="{src}" alt="{alt}" width="240" '
        f'style="display:block;width:100%;max-width:240px;height:auto;margin:0 auto;'
        f'border:1px solid #e5d9c8;border-radius:6px;background-color:#ffffff;">'
        f'</div></div>'
    )


def build_email_html(card, today):
    title = html.escape(card["title"])
    series = html.escape(card.get("series") or "")
    date = today.strftime("%A, %B %-d, %Y")

    sides = side_block(image_url(card["front"]), f"Front of the card: {title}")
    if card.get("back"):
        sides += side_block(image_url(card["back"]), f"Back of the card: {title}")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>Today's cigarette card</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f0e6;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">A little card to brighten your day.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f5f0e6;">
<tr><td align="center" style="padding:32px 16px;">

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
         style="max-width:600px;background-color:#fff9ef;border:1px solid #e5d9c8;border-radius:12px;">
    <tr><td style="padding:36px 32px 6px;text-align:center;">
      <p style="margin:0 0 6px;font-family:{SANS};font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#a35c37;">Cigarette Card Club</p>
      <p style="margin:0 0 22px;font-family:{SANS};font-size:13px;color:#8a7f75;">{date}</p>
      <p style="margin:0 0 22px;font-family:{SERIF};font-size:16px;line-height:1.5;font-style:italic;color:#5d534c;">Hello! I hope this card brings a little joy.</p>
      <h1 style="margin:0 0 8px;font-family:{SERIF};font-size:26px;line-height:1.25;font-weight:normal;color:#7c3c21;">{title}</h1>
      <p style="margin:0;font-family:{SANS};font-size:14px;line-height:1.5;color:#5d534c;">{series}</p>
    </td></tr>
    <tr><td align="center" style="padding:26px 15px 6px;font-size:0;line-height:0;">{sides}</td></tr>
    <tr><td style="padding:6px 32px 32px;text-align:center;font-family:{SANS};font-size:13px;line-height:1.6;color:#5d534c;">
      <p style="margin:0;">From the <a href="{card['link']}" style="color:#7c3c21;">New York Public Library Digital Collections</a>.</p>
    </td></tr>
  </table>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;">
    <tr><td style="padding:22px 16px 0;text-align:center;font-family:{SANS};font-size:12px;line-height:1.7;color:#8a7f75;">
      A new card every day from <a href="{SITE_URL}" style="color:#8a7f75;">cigarettecard.club</a>
      &nbsp;&middot;&nbsp; <a href="{{{{RESEND_UNSUBSCRIBE_URL}}}}" style="color:#8a7f75;">Unsubscribe</a>
    </td></tr>
  </table>

</td></tr>
</table>
</body>
</html>
"""


# --- Resend -----------------------------------------------------------------

def clean_tag_value(value):
    """Resend tag values allow only ASCII letters, numbers, underscores and dashes."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", str(value))
    return re.sub(r"_+", "_", cleaned).strip("_")[:49] or "untitled"


def send_broadcast(api_key, from_email, audience_id, subject, html_body, card):
    """Create a Resend broadcast and send it immediately. Returns the broadcast id."""
    resend.api_key = api_key
    created = resend.Broadcasts.create({
        "audience_id": audience_id,
        "from": from_email,
        "subject": subject,
        "html": html_body,
        "tags": [
            {"name": "content_type", "value": "cigarette_card"},
            {"name": "card_title", "value": clean_tag_value(card["title"])},
        ],
    })
    broadcast_id = created.get("id")
    if not broadcast_id:
        raise RuntimeError(f"Resend did not return a broadcast id: {created}")
    print(f"Created broadcast {broadcast_id}; sending...")
    resend.Broadcasts.send({"broadcast_id": broadcast_id})
    return broadcast_id


def send_test_email(api_key, from_email, to, subject, html_body):
    """Send the card to one address. Broadcast-only placeholders are replaced."""
    resend.api_key = api_key
    sent = resend.Emails.send({
        "from": from_email,
        "to": [to],
        "subject": subject,
        "html": html_body.replace("{{RESEND_UNSUBSCRIBE_URL}}", SITE_URL),
    })
    print(f"Test email sent to {to} (id {sent.get('id')})")


# --- Main -------------------------------------------------------------------

def main():
    load_dotenv()
    mode = os.getenv("MODE", "").lower()
    metadata_path = os.getenv("METADATA_PATH", "metadata.json")

    cards = load_cards(metadata_path)
    day = resolve_day()
    card = card_for_day(cards, day)
    print(f"{len(cards)} cards in pool; card for {day} is '{card['title']}' ({card['uuid']})")

    if mode == "preview":
        out = Path("preview_email.html")
        out.write_text(build_email_html(card, day))
        print(f"Preview written to {out}")
        return

    test_to = os.getenv("TEST_TO")
    needed = ("RESEND_API_KEY", "FROM_EMAIL") if test_to else ("RESEND_API_KEY", "RESEND_AUDIENCE_ID", "FROM_EMAIL")
    env = {k: os.getenv(k) for k in needed}
    missing = [k for k, v in env.items() if not v]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)}")

    max_attempts = 5
    tried = set()
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            card = fallback_card(cards, tried)
            print(f"\nAttempt {attempt}/{max_attempts}: falling back to '{card['title']}' ({card['uuid']})")
        tried.add(card["uuid"])
        try:
            verify_image(image_url(card["front"]))
            if card.get("back"):
                verify_image(image_url(card["back"]))
            html_body = build_email_html(card, day)
            if test_to:
                send_test_email(env["RESEND_API_KEY"], env["FROM_EMAIL"], test_to,
                                "today's cigarette card", html_body)
            else:
                send_broadcast(env["RESEND_API_KEY"], env["FROM_EMAIL"], env["RESEND_AUDIENCE_ID"],
                               "today's cigarette card", html_body, card)
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_attempts:
                sys.exit("All attempts failed.")
            time.sleep(2)
            continue

        print(f"Sent '{card['title']}'.")
        return


if __name__ == "__main__":
    main()
