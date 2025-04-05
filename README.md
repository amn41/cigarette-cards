# Daily Cigarette Cards

This project automatically posts historical cigarette cards to Substack. Cigarette cards were collectible cards included in cigarette packages between the 1870s and 1940s, covering various subjects from sports and nature to science and history. This bot shares one card daily from the New York Public Library's digital collection.

## Background

Cigarette cards were some of the world's first collectible cards, predating baseball cards and similar trading cards. Tobacco companies used them as both package stiffeners and marketing tools. The cards often came in themed sets and featured detailed illustrations and educational content on their backs, making them fascinating historical artifacts.

The New York Public Library has digitized over 100,000 cigarette cards, making them freely available through their Digital Collections API.

## Setup

### Prerequisites
- Python 3.7+
- A NYPL Digital Collections API token
- A Substack account

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/daily-cigarette-cards
cd daily-cigarette-cards
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Copy the example environment file and fill in your credentials:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Download the card metadata:
```bash
python download_metadata.py
```

This will create a `metadata.json` file containing information about all available cards in the collection.

### Required Files

- `metadata.json`: Contains the NYPL API response with card metadata
- `posted_cards.json`: Tracks which cards have been posted (created automatically)

## Usage

### Testing Locally

Run the script to create a single post scheduled for 3 minutes in the future:
```bash
python post_card.py
```

### Automation

To automate daily posts, you can set up a cron job or use a service like GitHub Actions. Example cron schedule:

```bash
0 9 * * * cd /path/to/repo && python post_card.py
```

This will run the script daily at 9 AM.

## How It Works

1. The script reads card metadata from a local JSON file
2. It selects a random unposted card
3. Downloads the high-resolution image from NYPL
4. Creates a Substack post with the title "A little card to brighten your day"
5. Schedules the post for publication
6. Records the card as posted to avoid duplicates

## Contributing

Contributions are welcome! Some areas that could use improvement:

- Better error handling
- Image preprocessing/optimization
- More detailed card descriptions
- Alternative scheduling strategies
- Support for different post formats

## Getting an API Token

To get a NYPL Digital Collections API token:
1. Visit [NYPL's Digital Collections API page](https://api.repo.nypl.org/)
2. Sign up for an account
3. Request an API token

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- New York Public Library for providing the Digital Collections API
- The unofficial Substack API library
- The tobacco companies of the late 19th/early 20th centuries for creating these fascinating historical artifacts

## Support

For questions or issues:
1. Open an issue in this repository
2. Contact [your contact info]