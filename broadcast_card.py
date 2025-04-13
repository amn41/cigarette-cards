import json
import random
import requests
import os
import re
import resend # Ensure resend is imported
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import time # Keep for retry delay

# --- NYPL Card Fetcher (Modified to return NYPL URL) ---
class NYPLCardFetcher:
    """Handles fetching random card data and image URL from NYPL."""

    def __init__(self, nypl_token, metadata_path='metadata.json', posted_path='posted_cards.json'):
        self.nypl_token = nypl_token
        self.metadata_path = Path(metadata_path)
        self.posted_path = Path(posted_path)
        # No headers needed for public image URLs
        self.metadata = self.load_json(self.metadata_path)
        self.posted_cards = self.load_json(self.posted_path, default=[])

    def load_json(self, path, default=None):
        """Load JSON data from a file."""
        try:
            path = Path(path)
            with path.open('r') as f: return json.load(f)
        except FileNotFoundError: print(f"Warning: File not found {path}"); return default or {}
        except json.JSONDecodeError: print(f"Warning: JSON decode error {path}"); return default or {}

    def save_posted_cards(self):
        """Save the list of posted cards."""
        try:
            with self.posted_path.open('w') as f: json.dump(self.posted_cards, f, indent=2)
        except Exception as e: print(f"Error saving posted cards to {self.posted_path}: {e}")

    def get_random_unposted_card(self):
        """Get data for a random unposted card."""
        try:
            captures = self.metadata.get('nyplAPI', {}).get('response', {}).get('capture', [])
            if not captures: raise ValueError("Metadata invalid or 'capture' empty.")

            available_cards = []
            for card in captures:
                 if (isinstance(card, dict) and
                     'uuid' in card and
                     'imageID' in card and
                     'title' in card and
                     card['uuid'] not in self.posted_cards):
                     available_cards.append(card)
        except Exception as e: raise Exception(f"Error processing metadata: {e}")

        if not available_cards:
            raise Exception("No valid, unposted cards with imageID remaining!")

        return random.choice(available_cards)

    def download_and_get_info(self, card_uuid):
        """
        Downloads card image locally for verification, gets title,
        and returns the direct NYPL image URL along with local path and title.
        """
        try:
            captures = self.metadata.get('nyplAPI', {}).get('response', {}).get('capture', [])
            card = next((i for i in captures if isinstance(i, dict) and i.get('uuid') == card_uuid), None)

            if not card: raise Exception(f"Card {card_uuid} not found in metadata")

            image_id = card.get('imageID')
            if not image_id: raise Exception(f"Card {card_uuid} is missing imageID")

            card_title = card.get('title', 'Untitled Card')
            print(f"Found imageID: {image_id} for card: {card_title}")

            # Construct the direct NYPL image URL (this is what we'll use in the email)
            nypl_image_url = f"https://images.nypl.org/index.php?id={image_id}&t=w"
            print(f"Image URL for email: {nypl_image_url}")

            # --- Download Step (for verification) ---
            print(f"Attempting download for verification from: {nypl_image_url}")
            response = requests.get(nypl_image_url, timeout=30)
            response.raise_for_status() # Check for HTTP errors

            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                raise Exception(f"Verification failed: Response is not an image. Content-Type: {content_type}")

            # Save temporarily (optional, but confirms download works)
            temp_path = f"temp_card_{re.sub(r'[^a-zA-Z0-9_-]', '_', card_uuid)}.jpg"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            print(f"Successfully verified and saved image locally to {temp_path}")
            # --- End Download Step ---

            # Return temp path (for cleanup), title, AND the public URL
            return temp_path, card_title, nypl_image_url

        except requests.exceptions.RequestException as e:
             raise Exception(f"Network error verifying/downloading image {nypl_image_url}: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to verify/download image for card {card_uuid}: {str(e)}")


# --- Resend Broadcast Sender (Using direct NYPL URL) ---
class ResendBroadcastSender:
    """Handles creating and sending emails via Resend Broadcast API"""

    def __init__(self, api_key, from_email, audience_id):
        self.api_key = api_key
        resend.api_key = api_key # Initialize resend globally
        self.from_email = from_email
        self.audience_id = audience_id

    def _clean_tag_value(self, value):
        """Clean tag value"""
        cleaned = re.sub(r'[^\w-]', '_', str(value))
        cleaned = re.sub(r'_+', '_', cleaned)
        return cleaned[:49]

    # Modified to accept nypl_image_url, image_path is now just for logging/reference
    def send_broadcast_card(self, image_path, card_title, nypl_image_url):
        """Creates AND immediately sends a broadcast email linking to the NYPL image."""
        created_broadcast_id = None # Initialize

        try:
            # === STEP 1: Create the Broadcast Definition ===

            # 1a. Image embedding/processing NO LONGER NEEDED here

            # 1b. Create HTML content using the direct NYPL URL
            html_content = f"""
            <html>
            <head>
                <title>A little card to brighten your day</title>
                 <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .card-container {{ text-align: center; margin: 30px 0; }}
                    img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
                    h1 {{ color: #444; }}
                    .footer {{ font-size: 14px; margin-top: 40px; color: #777; text-align: center; }}
                    .date {{ font-size: 14px; color: #888; margin-bottom: 30px; }}
                </style>
            </head>
            <body>
                <h1>A little card to brighten your day</h1>
                <div class="date">{datetime.now().strftime("%A, %B %d, %Y")}</div>
                <p>Hello!</p>
                <p>I hope this card brings a little joy.</p>
                <div class="card-container">
                    <img src="{nypl_image_url}" alt="{card_title}">
                    <p><em>{card_title}</em></p>
                </div>
                <p>This historical cigarette card is from the NYPL Digital Collections.</p>
                <div class="footer">
                    <p>Get a new card daily at cigarettecard.club!</p>
                    <p><a href="{{{{RESEND_UNSUBSCRIBE_URL}}}}">Unsubscribe</a></p>
                    <p>© cigarettecard.club</p>
                </div>
            </body>
            </html>
            """

            # 1c. Prepare 'create' parameters
            create_params: resend.Broadcasts.CreateParams = {
                "audience_id": self.audience_id,
                "from": self.from_email,
                "subject": f"today's cigarette card",
                "html": html_content,
                "tags": [
                    {"name": "content_type", "value": "cigarette_card"},
                    {"name": "card_title", "value": self._clean_tag_value(card_title)}
                ]
            }

            # 1d. Call 'create' API
            print(f"Creating broadcast definition for audience ID: {self.audience_id}...")
            created_broadcast = resend.Broadcasts.create(create_params)
            created_broadcast_id = created_broadcast.get('id')

            if not created_broadcast_id:
                 error_info = created_broadcast.get('error')
                 if error_info: raise Exception(f"Failed to create broadcast: {error_info.get('message', 'Unknown Resend error')}")
                 else: raise Exception("Failed to create broadcast: No ID or error received.")
            print(f"Broadcast definition created successfully! ID: {created_broadcast_id}")

            # === STEP 2: Send the Created Broadcast Immediately ===
            send_params: resend.Broadcasts.SendParams = {
                "broadcast_id": created_broadcast_id
            }
            print(f"Initiating sending for broadcast ID: {created_broadcast_id}...")
            send_response = resend.Broadcasts.send(send_params)

            if isinstance(send_response, dict) and send_response.get('id') == created_broadcast_id:
                 print(f"Broadcast sending initiated successfully! Response ID: {send_response.get('id')}")
            else:
                 print(f"Broadcast sending initiated. Response: {send_response}")

            return created_broadcast # Return create response

        # ----- Generic Error Handling -----
        except Exception as e:
            if created_broadcast_id:
                 print(f"Error during broadcast process (Create OK, ID: {created_broadcast_id}, Send failed): {str(e)}")
            else:
                 print(f"Error during broadcast creation step: {str(e)}")
            raise

# --- Main Execution Logic ---
def main():
    """Fetches card, verifies image, sends broadcast linking to NYPL image."""
    load_dotenv()

    # Get config from .env
    nypl_token = os.getenv("NYPL_TOKEN") # Keep handy if needed later
    resend_api_key = os.getenv("RESEND_API_KEY")
    resend_audience_id = os.getenv("RESEND_AUDIENCE_ID") # For Broadcast
    from_email = os.getenv("FROM_EMAIL")
    metadata_path = os.getenv("METADATA_PATH", "metadata.json")
    posted_path = os.getenv("POSTED_PATH", "posted_cards.json")

    # Validate required vars for broadcast
    required_vars = {
        "RESEND_API_KEY": resend_api_key,
        "RESEND_AUDIENCE_ID": resend_audience_id,
        "FROM_EMAIL": from_email
    }
    missing_vars = [name for name, value in required_vars.items() if not value]
    if missing_vars:
        raise Exception(f"Missing env variables for broadcast: {', '.join(missing_vars)}!")

    # Initialize
    card_fetcher = NYPLCardFetcher(nypl_token, metadata_path, posted_path)
    broadcast_sender = ResendBroadcastSender(resend_api_key, from_email, resend_audience_id)

    # Retry logic
    max_attempts = 5
    image_path = None # To store temp path for cleanup

    for attempt in range(1, max_attempts + 1):
        print(f"\nAttempt {attempt} of {max_attempts}")
        card_uuid = None # Ensure defined in scope

        try:
            # 1. Get random card data
            card_data = card_fetcher.get_random_unposted_card()
            card_uuid = card_data.get('uuid')
            if not card_uuid:
                 print("Skipping card with missing UUID.")
                 continue # Try next attempt directly

            # Check if failed previously this run (optional, depends on retry strategy)
            # if card_uuid in failed_cards: continue

            print(f"Selected card: {card_data.get('title', 'N/A')} (UUID: {card_uuid})")

            # 2. Verify/download image and get its direct NYPL URL
            #    We download locally mainly to confirm the image exists and is valid
            image_path, fetched_card_title, nypl_image_url = card_fetcher.download_and_get_info(card_uuid)
            print(f"Verified image is accessible at: {nypl_image_url}")

            # 3. Create AND Send broadcast linking to the NYPL URL
            #    Pass image_path mainly for reference/logging if needed inside sender
            broadcast_sender.send_broadcast_card(image_path, fetched_card_title, nypl_image_url)

            # 4. Record card as posted
            if os.getenv("MODE") != "test":
                card_fetcher.posted_cards.append(card_uuid)
                card_fetcher.save_posted_cards()
                print(f"Marked card {card_uuid} as posted.")
            else:
                 print("Test mode: Card not marked as posted.")

            # Success!
            print(f"Broadcast for card '{fetched_card_title}' created and sent successfully!")
            break # Exit retry loop

        except Exception as e:
            print(f"Error during attempt {attempt}: {str(e)}")
            # Simple retry, add card UUID to failed list if needed
            if attempt == max_attempts:
                print("All attempts failed for this run.")
            else:
                 print("Retrying...")
                 time.sleep(2)

        finally:
            # Cleanup temporary image file if it was created
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"Cleaned up temporary file: {image_path}")
                    image_path = None # Reset path
                except OSError as e:
                    print(f"Warning: Could not remove temp file {image_path}: {e}")

if __name__ == "__main__":
    main()
