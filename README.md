# Daily Cigarette Cards

This is a simple newsletter service using Resend for emails and managing signups via a simple netlify function.

## Background

Cigarette cards were some of the world's first collectible cards, predating baseball cards and similar trading cards. Tobacco companies used them as both package stiffeners and marketing tools. The cards often came in themed sets and featured detailed illustrations and educational content on their backs, making them fascinating historical artifacts.

The New York Public Library has digitized over 100,000 cigarette cards, making them freely available through their Digital Collections API.


## Setup

Emails are sent via a GitHub Action `.github/workflows/daily_card.yml`, and require the following API keys:

* `RESEND_API_KEY`: Your Resend API key (e.g., `re_...`). **Required**.
* `RESEND_AUDIENCE_ID`: The ID of your Resend Audience to send the broadcast to. **Required**.
* `FROM_EMAIL`: The verified email address Resend will use in the "From" field (e.g., `"Your Name <sender@yourverifieddomain.com>"`). **Required**.
* `NYPL_TOKEN`: Your NYPL API token. *(Optional, currently only needed if you modify the script to make authenticated NYPL API calls)*.

To avoid sending duplicate cards, the script tracks the UUIDs of sent cards in a file named `posted_cards.json` as a github artifact.

## ▶️ Running Locally

1.  Create a `.env` file with your environment variables
2.  Make sure your virtual environment is activated.
3.  Run the script:
    ```bash
    python broadcast_card.py
    ```
4.  This will execute the script once, sending an email (if not in test mode) and updating the local `posted_cards.json` file.


## 🙏 Acknowledgments

* Card images and metadata are sourced from the [New York Public Library Digital Collections](https://digitalcollections.nypl.org/). Thank you, NYPL!
* Email delivery powered by [Resend](https://resend.com/).

---
