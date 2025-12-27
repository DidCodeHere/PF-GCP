# Smart Property Finder

A CLI tool for finding below-market-value investment properties (flats, houses, land) in the UK.

## Features
- Scrapes Rightmove for properties under a price cap (default £100k).
- "Smart Analysis" to highlight renovation/development opportunities based on keywords.
- Filters for Freehold (best effort based on description).
- Export to CSV.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script from the root directory:

```bash
python -m src.main
```

Or with arguments:

```bash
python -m src.main --location "Liverpool" --radius 10 --max-price 80000
```

## Note on Scraping
This tool uses standard web requests. If Rightmove blocks the requests (403 Forbidden), you may need to wait or implement the Playwright-based scraper (outlined in project white paper).
