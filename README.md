# GCP Investment Finder 🏠

[![GitHub Actions](https://github.com/DidCodeHere/PF-GCP/actions/workflows/scrape.yml/badge.svg)](https://github.com/DidCodeHere/PF-GCP/actions/workflows/scrape.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**GCP Investment Finder** (formerly Smart Property Finder) is an advanced, open-source tool designed to automate the discovery of high-potential, below-market-value (BMV) investment properties across the UK.

🔗 **[View Live Dashboard](https://didcodehere.github.io/PF-GCP/)**

---

## 🚀 Overview

Finding the right investment property usually involves trawling through thousands of listings on Rightmove, Zoopla, and various auction sites. **GCP Investment Finder** automates this process.

It scrapes major UK property portals and auction houses, aggregates the data, and uses smart heuristic analysis (and optional Local LLMs) to identify properties with **renovation potential**, **distressed sales**, and **auction opportunities**.

### Key Features

- **Nationwide Coverage**: Scrapes properties from 40+ major UK cities and nationwide auction houses.
- **Multi-Source Aggregation**:
  - Rightmove & Zoopla
  - OnTheMarket
  - Boomin & Purplebricks
  - **Auctions**: Auction House UK, Pugh & Co, SDL Auctions, Allsop.
- **Smart Analysis**: Automatically scores properties based on keywords (e.g., "modernisation required", "fire damaged", "repossession").
- **Web Dashboard**: A clean, responsive web interface to filter and sort opportunities by ROI potential.
- **Automated Updates**: Runs daily via GitHub Actions to ensure fresh data.
- **Free & Open Source**: Designed to run entirely on free infrastructure (GitHub Pages + Actions).

## 🛠️ Installation

### Prerequisites

- Python 3.10 or higher
- Google Chrome (for Playwright)

### Setup

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/DidCodeHere/PF-GCP.git
    cd PF-GCP
    ```

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers**:
    ```bash
    playwright install chromium
    ```

## 💻 Usage

### Web Scraper (Recommended)

To run the full scraping pipeline that powers the web dashboard:

```bash
python scripts/scrape_for_web.py --locations "england" --max-price 150000
```

_This will generate a `data/properties.json` file._

### CLI Tool

For quick, interactive searches in your terminal:

```bash
python -m src.main search --location "Manchester" --radius 5 --max-price 100000
```

## 📊 Data Sources

We currently support scraping from:

- **Portals**: Rightmove, Zoopla, OnTheMarket, Boomin, Purplebricks.
- **Auctions**: Auction House UK, Pugh & Co, SDL Auctions, Allsop.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

_Disclaimer: This tool is for educational and research purposes only. Please respect the terms of service of the websites you scrape._
