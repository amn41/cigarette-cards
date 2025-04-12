# Daily Cigarette Cards

This project automatically posts historical cigarette cards to Substack. Cigarette cards were collectible cards included in cigarette packages between the 1870s and 1940s, covering various subjects from sports and nature to science and history. This bot shares one card daily from the New York Public Library's digital collection.

## Background

Cigarette cards were some of the world's first collectible cards, predating baseball cards and similar trading cards. Tobacco companies used them as both package stiffeners and marketing tools. The cards often came in themed sets and featured detailed illustrations and educational content on their backs, making them fascinating historical artifacts.

The New York Public Library has digitized over 100,000 cigarette cards, making them freely available through their Digital Collections API.


# Daily NYPL Cigarette Card Email 🚬✉️

[![Daily Card Workflow](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/actions/workflows/daily_card.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/actions/workflows/daily_card.yml)

A simple Python application that automatically sends a daily email featuring a random vintage cigarette card image sourced from the [New York Public Library's Digital Collections](https://digitalcollections.nypl.org/). The emails are sent using the [Resend](https://resend.com/) API via their Broadcast functionality.

---

## ✨ Features

* **Daily Automation:** Uses GitHub Actions to run automatically once per day.
* **Random Selection:** Picks a random cigarette card from the NYPL collection metadata.
* **Duplicate Prevention:** Keeps track of previously sent cards to avoid duplicates (using GitHub Action artifacts).
* **Direct Image Linking:** Uses direct image URLs from NYPL Digital Collections.
* **Resend Broadcast API:** Leverages the Resend Broadcast API to send emails to a predefined audience.
* **Easy Setup:** Requires minimal configuration via GitHub Secrets.

## 🚀 Technology Stack

* **Python 3:** Core application language.
* **Requests:** For fetching/verifying image URLs.
* **Resend Python SDK:** For interacting with the Resend API.
* **GitHub Actions:** For daily automation and state management via artifacts.

## 🔧 Setup and Installation

Follow these steps to set up the project, either for local testing or before deploying the GitHub Action.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
    cd YOUR_REPO_NAME
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Obtain Metadata:**
    * This project relies on a `metadata.json` file containing data scraped or downloaded from the NYPL Digital Collections API for relevant items (like cigarette cards).
    * This repository includes a `metadata.json` file. If you need to regenerate or update it, you would typically use a separate script to query the NYPL API. *(You can add details here if you have such a script)*.

5.  **Set up Resend:**
    * Create a [Resend account](https://resend.com/).
    * Verify your sending domain (e.g., `yourdomain.com`).
    * Create an API Key.
    * Create an Audience and note its Audience ID. Add contacts to this audience who should receive the emails.

## 🔑 Configuration

Configuration is primarily handled via GitHub Secrets for the automated workflow. For local testing, you can use a `.env` file.

### GitHub Secrets (for Automation)

Go to your repository's `Settings` > `Secrets and variables` > `Actions` and add the following secrets:

* `RESEND_API_KEY`: Your Resend API key (e.g., `re_...`). **Required**.
* `RESEND_AUDIENCE_ID`: The ID of your Resend Audience to send the broadcast to. **Required**.
* `FROM_EMAIL`: The verified email address Resend will use in the "From" field (e.g., `"Your Name <sender@yourverifieddomain.com>"`). **Required**.
* `NYPL_TOKEN`: Your NYPL API token. *(Optional, currently only needed if you modify the script to make authenticated NYPL API calls)*.

### `.env` File (for Local Testing)

1.  Create a file named `.env` in the root directory.
2.  Add the following variables (replace with your actual values):

    ```dotenv
    # .env file
    RESEND_API_KEY="re_YOUR_RESEND_API_KEY"
    RESEND_AUDIENCE_ID="YOUR_RESEND_AUDIENCE_ID"
    FROM_EMAIL="Your Name <sender@yourverifieddomain.com>"
    # NYPL_TOKEN="YOUR_NYPL_TOKEN" # Optional

    # Optional: Override default file paths if needed
    # METADATA_PATH="path/to/your/metadata.json"
    # POSTED_PATH="path/to/your/posted_cards.json"
    # MODE="test" # Set to prevent updating posted_cards.json locally
    ```
3.  **Important:** Ensure `.env` is listed in your `.gitignore` file to avoid committing secrets.

## 🤖 Automation with GitHub Actions

This project uses the GitHub Action defined in `.github/workflows/daily_card.yml`.

* **Schedule:** It's configured to run automatically once a day at a specified time (default is 14:00 UTC - adjust the `cron` schedule in the file if needed). Remember that GitHub Actions schedules use **UTC time**.
* **Manual Trigger:** You can also trigger it manually from the "Actions" tab in your GitHub repository (`workflow_dispatch`).
* **Secrets:** It uses the GitHub Secrets you configured for API keys and other sensitive information.
* **State Management:** It uses artifacts to manage the list of sent cards (see below).

## 💾 State Management: `posted_cards.json`

To avoid sending duplicate cards, the script tracks the UUIDs of sent cards in a file named `posted_cards.json`.

* **`.gitignore`:** This file is intentionally listed in `.gitignore` to prevent the constantly changing state from being committed to the repository history.
* **GitHub Actions Artifacts:** The `daily_card.yml` workflow handles state persistence between runs:
    1.  **Download:** At the start of a run, it attempts to download the `posted-cards-state` artifact from the previous successful run.
    2.  **Prepare:** If the artifact doesn't exist (first run) or download fails, it creates a new `posted_cards.json` containing `[]`. Otherwise, it uses the downloaded file.
    3.  **Execute:** The `broadcast_card.py` script reads this file, selects a card not in the list, and appends the new card's UUID to the list within the script's logic.
    4.  **Upload:** If the script completes successfully, the *updated* `posted_cards.json` file is uploaded as the `posted-cards-state` artifact for the next run.
* **Limitations:**
    * Artifacts have a retention period (default 90 days for free/pro accounts). If the action doesn't run successfully for longer than that, the state might be lost.
    * If the script fails *after* sending the email but *before* the artifact upload step completes, the state won't be saved, potentially leading to a duplicate on the next run. For higher reliability, consider using external storage (like S3 or a database) for state.

## ▶️ Running Locally

1.  Ensure you have set up the `.env` file as described in Configuration.
2.  Make sure your virtual environment is activated.
3.  Run the script:
    ```bash
    python broadcast_card.py
    ```
4.  This will execute the script once, sending an email (if not in test mode) and updating the local `posted_cards.json` file.

## 🙌 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue. (Add more specific contribution guidelines if desired).

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details (or add license text here).

**Recommendation:** Create a `LICENSE` file in your repository containing the MIT License text. [Choosealicense.com](https://choosealicense.com/licenses/mit/) is a helpful resource.

## 🙏 Acknowledgments

* Card images and metadata are sourced from the [New York Public Library Digital Collections](https://digitalcollections.nypl.org/). Thank you, NYPL!
* Email delivery powered by [Resend](https://resend.com/).

---