import json
import requests
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import os
import time

def download_metadata():
    # Load environment variables
    dotenv_path = find_dotenv()
    print(f"Loading .env from: {dotenv_path}")
    load_dotenv(dotenv_path)

    # Get token from environment
    token = os.getenv("NYPL_TOKEN")
    if not token:
        raise ValueError("NYPL_TOKEN not found in .env file")

    # API configuration
    headers = {
        'Authorization': f'Token token="{token}"'
    }

    collections = [
        "b686cfd0-c52b-012f-c9e6-58d385a7bc34",  # ABC of Sports collection
        "b2d37b40-c52d-012f-f8ec-58d385a7bc34",  # aeroplanes
        "1615ed60-c52e-012f-6579-58d385a7bc34",  # subcollection 1
        "53249090-c52e-012f-65dd-58d385a7bc34",  # subcollection 2
        "66052980-c52e-012f-6d83-58d385a7bc34",  # subcollection 3
        "70423dd0-c52e-012f-7733-58d385a7bc34",  # subcollection 4
        "161d80e0-c52f-012f-c7a8-58d385a7bc34",  # subcollection 5
        "4b853b70-c52f-012f-8f45-58d385a7bc34",  # subcollection 6
        "6a3d3310-c52f-012f-5440-58d385a7bc34",  # subcollection 7
        "949f5dd0-c52f-012f-ddb5-58d385a7bc34",  # subcollection 8
        "b893ce70-c52f-012f-e3f5-58d385a7bc34",  # subcollection 9
        "d3194c20-c52f-012f-afdd-58d385a7bc34",  # subcollection 10
        "1b587dd0-c530-012f-90d8-58d385a7bc34",  # subcollection 11
        "e79eb2f0-c52f-012f-457c-58d385a7bc34",  # subcollection 12
        "dc5124e0-c530-012f-32bb-58d385a7bc34",  # subcollection 13
        "462cc620-c531-012f-3e1e-58d385a7bc34",  # subcollection 14
        "5ac13e00-c531-012f-bfa4-58d385a7bc34",  # subcollection 15
        "dd0a2fe0-c531-012f-cfa6-58d385a7bc34",  # subcollection 16
        "392972e0-c532-012f-5aa1-58d385a7bc34",  # subcollection 17
        "97b79410-c536-012f-b383-58d385a7bc34",  # subcollection 18
        "d2e1ded0-c538-012f-c313-58d385a7bc34",  # subcollection 19
        "342d4e10-c53a-012f-fd64-58d385a7bc34",  # subcollection 20
        "58ed9c40-c53b-012f-6ce6-58d385a7bc34",  # subcollection 21
        "e8dbd7b0-c53d-012f-33ad-58d385a7bc34",  # subcollection 22
        "8ee1f5e0-c540-012f-2b4a-58d385a7bc34",  # subcollection 23
        "f810dc20-c540-012f-9860-58d385a7bc34",  # subcollection 24
        "59ea7730-c541-012f-6b46-58d385a7bc34",  # subcollection 25
        "c78c1e00-c541-012f-136c-58d385a7bc34",  # subcollection 26
        "c91d85e0-c542-012f-d78f-58d385a7bc34",  # subcollection 27
        "7e984420-c543-012f-faab-58d385a7bc34",  # subcollection 28
        "8e6c5710-c546-012f-a0d9-58d385a7bc34",  # subcollection 29
        "02335b50-c54b-012f-023e-58d385a7bc34",  # subcollection 30
        "bbd87f50-c54f-012f-1287-58d385a7bc34",  # subcollection 31
        "cdde0960-c54f-012f-7496-58d385a7bc34",  # subcollection 32
        "e0b102e0-c54f-012f-b5c7-58d385a7bc34",  # subcollection 33
        "f2c8f600-c54f-012f-21c0-58d385a7bc34",  # subcollection 34
        "a77d95e0-c550-012f-22a4-58d385a7bc34",  # subcollection 35
        "55b6ffe0-c552-012f-3cf9-58d385a7bc34",  # subcollection 36
        "0e7fc620-c566-012f-9810-58d385a7bc34",  # subcollection 37
        "14a20990-c566-012f-4d9d-58d385a7bc34",  # subcollection 38
        "6f502ef0-c569-012f-b7a6-58d385a7bc34",  # subcollection 39
        "c3b91e70-c569-012f-5457-58d385a7bc34",  # subcollection 40
        "57089220-c56e-012f-5ac6-58d385a7bc34",  # subcollection 41
        "0f260db0-c56f-012f-e9ba-58d385a7bc34",  # subcollection 42
        "553c9d60-c56f-012f-bf7f-58d385a7bc34",  # subcollection 43
        "13eabc60-c573-012f-f721-58d385a7bc34",  # subcollection 44
        "79c06ed0-c5a0-012f-c9d7-58d385a7bc34",  # subcollection 45
    ]

    all_collections_data = {}

    for collection_uuid in collections:
        print(f"\n{'='*60}")
        print(f"Processing collection: {collection_uuid}")
        print(f"{'='*60}")

        base_url = f"https://api.repo.nypl.org/api/v2/items/{collection_uuid}"

        all_items = []
        page = 1
        per_page = 50  # Adjust if needed

        print("Downloading metadata...")

        while True:
            print(f"\nFetching page {page}...")

            # Make API request
            params = {
                'page': page,
                'per_page': per_page
            }

            try:
                response = requests.get(base_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                # Extract items from response
                items = data['nyplAPI']['response']['capture']
                if not items:
                    print("No more items found.")
                    break

                print(f"Found {len(items)} items on this page")
                all_items.extend(items)
                print(f"Total items so far: {len(all_items)}")

                # Check if we've reached the total number of pages
                total_pages = int(data['nyplAPI']['request'].get('totalPages', 1))
                if page >= total_pages:
                    print(f"Reached last page ({total_pages})")
                    break

                page += 1
                time.sleep(1)  # Be nice to the API

            except KeyError as e:
                print(f"Unexpected response structure. KeyError: {e}")
                print("Full response:", json.dumps(data, indent=2))
                break
            except requests.exceptions.RequestException as e:
                print(f"Request failed for collection {collection_uuid}: {e}")
                break

        # Store data for this collection
        if all_items:
            all_collections_data[collection_uuid] = {
                "nyplAPI": {
                    "response": {
                        "capture": all_items
                    }
                }
            }
            print(f"Collection {collection_uuid}: {len(all_items)} items downloaded")
        else:
            print(f"No items downloaded for collection {collection_uuid}")

    # Save all collections data
    if all_collections_data:
        # Save individual collection files
        for collection_uuid, metadata in all_collections_data.items():
            output_path = Path(f"metadata_{collection_uuid}.json")
            with open(output_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Collection {collection_uuid} saved to: {output_path}")

        # Save combined file
        combined_output_path = Path("metadata_all_collections.json")
        with open(combined_output_path, 'w') as f:
            json.dump(all_collections_data, f, indent=2)

        print(f"\n{'='*60}")
        print("Download complete!")
        print(f"Total collections processed: {len(all_collections_data)}")
        total_items = sum(len(data['nyplAPI']['response']['capture']) for data in all_collections_data.values())
        print(f"Total items downloaded: {total_items}")
        print(f"Combined metadata saved to: {combined_output_path}")
        print(f"Individual collection files also saved.")
    else:
        print("No items were downloaded from any collection. Please check the API response structure.")

if __name__ == "__main__":
    download_metadata()
