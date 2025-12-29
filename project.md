# Project White Paper: Smart Property Finder

## 1. Executive Summary

The **Smart Property Finder** is a tool designed for construction companies and property investors. Its primary mission is to automate the discovery of high-potential, low-cost investment opportunities in the UK property market. Specifically, it targets freehold properties (flats, houses, land) under £100,000 that require renovation or development.

The system is available both as a **Command-Line Interface (CLI)** for power users and a **Web Interface** hosted on GitHub Pages for broader accessibility.

By leveraging web scraping technologies (with optional API integration where available) and Artificial Intelligence (AI), the system identifies properties that traditional filters might miss, focusing on description analysis to find "fixer-uppers" and development deals.

> **Design Principle**: This project is designed to be **100% free** to run. No paid APIs, no hosting costs. GitHub Pages for the frontend, GitHub Actions for scheduled scraping, and free-tier LLMs for analysis.

## 2. Work Done

- [x] **Project Initialization**: Established repository structure and version control.
- [x] **Requirements Definition**: Outlined core features, target platforms, and AI integration strategy.
- [x] **Scraper Implementation**: Developed robust scraping modules for Rightmove and Zoopla using browser automation (Playwright).
- [x] **Heuristic Analyzer**: Implemented keyword-based scoring system to identify renovation potential.
- [x] **CLI Interface**: Created command-line entry points for user interaction using `typer` and `rich`.
- [x] **AI Analyzer Engine**: Integrated `ollama` to use local LLMs (e.g., Llama 3) for semantic analysis of property descriptions.
- [x] **Zoopla Support**: Added scraping capabilities for Zoopla to expand property search.
- [x] **Auction Integration**: Added scrapers for Auction House UK and Pugh & Co to find distressed assets.
- [x] **Smart Radius**: Implemented auto-expanding search radius if initial results are low.
- [x] **Land Filtering**: Improved scoring to penalize land-only plots and added strict exclusion filter.
- [x] **Default to All Sources**: Updated CLI to search all available sources (Rightmove, Zoopla, Auctions) by default.
- [x] **Timeout Protection**: Added 20-second default timeouts to all scrapers to prevent infinite hanging.
- [x] **Selector Optimization**: Fixed Auction House scraper to target specific result containers (~50 results) instead of iterating thousands of links.
- [x] **Web Interface**: Created static HTML/CSS/JS frontend for GitHub Pages deployment.
- [x] **JSON Exporter**: Added `src/json_exporter.py` for converting scraped data to JSON format.
- [x] **GitHub Actions Workflow**: Created `.github/workflows/scrape.yml` for automated daily scraping.
- [x] **OnTheMarket Scraper**: Added new source `search_onthemarket()` method.
- [x] **Nestoria API Scraper**: Implemented API-based scraper (currently disabled due to API SSL issues).
- [x] **Exclude Auctions Filter**: Added web interface toggle to hide all auction properties with smart keyword detection.
- [x] **Nationwide England Search**: Default search now covers 40+ major English cities across all regions.
- [x] **Boomin Scraper**: Added `search_boomin()` method for the newer UK property portal.
- [x] **Purplebricks Scraper**: Added `search_purplebricks()` for the major online estate agent.
- [x] **Price Range Expansion**: Increased default max price to £150,000 for broader coverage.
- [x] **SDL Auctions Scraper**: Added `search_sdl_auctions()` for one of UK's largest auctioneers.
- [x] **Allsop Auctions Scraper**: Added `search_allsop()` for major UK auction house.
- [x] **Min Price Filter**: Added minimum price slider to web interface.
- [x] **Tenure Filter**: Added freehold/leasehold filter checkboxes to web interface.
- [x] **Scrape Speed Optimization**: Refactored scraping logic to run auction searches nationwide once, significantly reducing redundant requests.
- [x] **Advanced Deduplication**: Implemented URL-based deduplication to ensure unique property listings across multiple sources.

## 3. Feature Requirements

### 3.1. Core Functionality

- **Search Capabilities**:
  - Input: Location (Postcode or Town) and Search Radius (miles).
  - Filters: Max Price (£150,000), Tenure (Freehold), Property Type (Houses, Flats, Land).
- **Data Acquisition (Scraping)**:
  - Must handle dynamic HTML content (Single Page Applications).
  - Resilience against basic anti-scraping measures (User-Agent rotation, rate limiting).
  - Extract: Price, Address, Description, Agent Link, Tenure.

### 3.2. AI & Smart Analysis

- **Model Selection**: Use a lightweight, open-source model (e.g., Llama 3 via Ollama, or GPT4All) to run locally without API costs.
- **Analysis Logic**:
  - **High Priority**: "Unlivable", "Derelict", "Fire Damaged", "Structural Issues", "Repossession", "Auction".
  - **Medium Priority**: "Modernisation", "Refurbishment", "Fixer Upper".
  - **Logic**:
    - Assign significantly higher scores (weight +3) to properties marked as unlivable or having structural issues, as these offer the best margins for a construction company.
    - Assign standard scores (weight +1.5) to cosmetic fixers.
  - Filter out "Shared Ownership" or "Leasehold" if they slip through initial filters.

### 3.3. User Interface (CLI)

- **Interactive Mode**: Prompts user for inputs if arguments aren't provided.
- **Output**:
  - Sorted list (cheapest first) of identified opportunities.
  - Display format:
    ```text
    [Score: 9/10] £85,000 - 3 Bed Terrace, Manchester (Freehold)
    Summary: "Requires full modernisation. Great rental potential."
    Link: https://rightmove.co.uk/...
    ```
  - Option to save results to a CSV file.

## 4. Technical Architecture

- **Language**: Python 3.10+
- **Scraping Engine**: `playwright` (for rendering JS) + `beautifulsoup4` (for parsing).
- **AI Engine**: `ollama` (interface to local LLM) or heuristic NLP as a fallback.
- **Dependencies**: `typer` (CLI), `pandas` (Data handling), `rich` (Terminal formatting).

## 5. Roadmap

1.  **Phase 1**: Build the scraper for Rightmove (most popular). [Completed]
2.  **Phase 2**: Implement keyword-based scoring (heuristic). [Completed]
3.  **Phase 3**: Integrate Local LLM for semantic analysis. [Completed]
4.  **Phase 4**: Add Zoopla support and export features. [Completed]
5.  **Phase 5**: Refinements & Improvements. [Completed]
    - [x] **Land Scoring**: Adjust scoring logic to prioritize residential properties over land.
    - [x] **CLI UX**: Include direct property links in the terminal output.
6.  **Phase 6**: Usability & Intelligence Overhaul [Completed]
    - [x] **Smart Radius Expansion**: Automatically increase search area if insufficient residential properties are found.
    - [x] **Strict Filtering**: Option to completely exclude land/commercial listings.
    - [x] **Enhanced Categorization**: Visual tags for "Ready to Rent", "Fixer Upper", etc.
    - [ ] **Interactive Config**: Allow users to adjust scoring weights via CLI. (Moved to Future Work)

## 6. Improvements & Refinements

- **Land Penalty**: Land investments are now scored significantly lower (-10 points) to ensure they appear below residential properties.
- **CLI Links**: The results table now includes a clickable URL for each property.
- **Smart Radius**: Automatically expands search radius (up to 40 miles) if fewer than 3 residential properties are found.
- **Interactive Mode**: The CLI now defaults to an interactive wizard if arguments are missing, asking about land exclusion and AI usage.
- **Strict Filtering**: Added `--exclude-land` flag (and interactive prompt) to completely remove land listings.
- **Categorization**: Properties are now visually categorized as "Distressed", "Fixer Upper", "Land", or "Standard".

## 7. Future Work

- **Interactive Config**: Allow users to adjust scoring weights via CLI.

---

## 8. Phase 8: Web Interface & GitHub Pages Deployment

### 8.1 Objective

Refactor the project to support a **Web Interface** hosted on **GitHub Pages**. This allows users to access the property finder without needing Python or CLI expertise.

### 8.2 Requirements

- **100% Static & Free**: No servers, no paid services. Everything runs on GitHub's free tier.
- **Architecture**:
  - **Frontend**: Pure HTML/CSS/JS served by GitHub Pages. No build step required.
  - **Backend**: None at runtime. All data is pre-generated.
  - **Data Pipeline**: GitHub Actions runs the Python scraper on a schedule (e.g., daily) and commits the results as JSON files to the repo.
  - **Data Layer**: Static JSON files (`/data/*.json`) loaded by the frontend via `fetch()`.
- **Cost**: $0. GitHub Pages and Actions are free for public repos.
- **User Experience**:
  - Search form: Location, Max Price, Radius, Source filters.
  - Results displayed as interactive cards with sorting/filtering.
  - Mobile-responsive design.
  - All filtering happens client-side in JavaScript (no server calls).

### 8.3 File Structure for GitHub Pages

```
/
├── index.html              # Main entry point
├── assets/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js          # Frontend logic (fetch JSON, render results)
├── data/
│   └── properties.json     # Pre-scraped data (updated via GitHub Actions)
├── src/                    # Existing Python backend (CLI + scraping)
└── .github/
    └── workflows/
        └── scrape.yml      # Scheduled action to refresh property data
```

### 8.4 Tasks

- [x] Create `index.html` with search form and results container.
- [x] Build `app.js` to load `properties.json` and render filterable results.
- [x] Create `style.css` with responsive mobile-first design.
- [x] Set up GitHub Actions workflow to run scraper daily and commit updated JSON.
- [x] Create `scripts/scrape_for_web.py` with timeout protection.
- [x] Ensure CLI remains functional alongside web interface.
- [x] Add "Exclude All Auctions" quick filter toggle to web interface.
- [x] Add nationwide "england" search mode covering 40+ cities across all regions.
- [x] Add data freshness panel showing "Last Updated" and "Next Refresh" countdown.
- [x] Add manual refresh button linking to GitHub Actions workflow.

### 8.5 Nationwide Search Coverage

When `--locations england` is specified (now the default), the scraper searches these cities:

| Region          | Cities                                                            |
| --------------- | ----------------------------------------------------------------- |
| North West      | Liverpool, Manchester, Preston, Blackpool, Bolton, Wigan          |
| North East      | Newcastle, Sunderland, Middlesbrough, Durham                      |
| Yorkshire       | Leeds, Sheffield, Bradford, Hull, York, Doncaster                 |
| East Midlands   | Nottingham, Leicester, Derby, Lincoln                             |
| West Midlands   | Birmingham, Coventry, Wolverhampton, Stoke-on-Trent               |
| East of England | Norwich, Cambridge, Ipswich, Peterborough                         |
| South East      | Brighton, Southampton, Portsmouth, Reading, Oxford, Milton Keynes |
| South West      | Bristol, Plymouth, Exeter, Bournemouth, Gloucester                |
| Greater London  | Croydon, Barking, Dagenham (affordable outer boroughs)            |

---

## 9. Phase 9: Scraping Method Improvement (API as Enhancement)

### 9.1 Current Approach

The primary scraping method uses **browser automation (Playwright)** to load web pages and extract data. This is the **default and reliable** approach that works universally.

**Playwright Scraping (Primary)**:

- ✅ Works on any website regardless of tech stack.
- ✅ Handles JavaScript-rendered content.
- ⚠️ Slower (5-20 seconds per source).
- ⚠️ HTML changes can break selectors.

### 9.2 API Scraping (Secondary/Optional)

Some property websites expose **internal APIs** (JSON endpoints) that can be used _when discoverable_. This is an **optional enhancement**, not a replacement.

**API Scraping (When Available)**:

- ✅ Faster: Direct HTTP requests, no browser needed.
- ✅ More stable: APIs change less often than UI.
- ⚠️ Not all sites have accessible APIs.
- ⚠️ APIs may require authentication or have rate limits.

> **Important**: API scraping is **opportunistic**. We only use it when an API is confirmed to exist and is freely accessible. Playwright remains the fallback for all sources.

### 9.3 Source Status

| Source        | Primary Method    | API Available? | Notes                                       |
| ------------- | ----------------- | -------------- | ------------------------------------------- |
| Rightmove     | Playwright + JSON | ✅ Partial     | `__NEXT_DATA__` embeds JSON in page source. |
| Zoopla        | Playwright + HTML | ❓ To Check    | May have internal API, needs investigation. |
| OnTheMarket   | Playwright + DOM  | ✅ Implemented | Working scraper added.                      |
| Auction House | Playwright + DOM  | ❌ None        | No public API found.                        |
| Pugh Auctions | Playwright + DOM  | ❌ None        | No public API found.                        |
| Nestoria      | httpx API         | ⚠️ Down        | API exists but SSL issues (server-side).    |
| Purplebricks  | Not Implemented   | ❓ To Check    | Check before implementing.                  |

### 9.4 Tasks

- [x] Implement OnTheMarket scraper with Playwright.
- [x] Implement Nestoria API scraper with httpx (disabled due to API downtime).
- [ ] **Audit each source** for hidden API endpoints (browser DevTools > Network tab).
- [ ] Document which sources have usable APIs vs. require Playwright.
- [ ] For sources with APIs: Create lightweight `httpx`-based scrapers.
- [ ] Keep Playwright scrapers as fallback for all sources.
- [ ] Add request caching to avoid redundant calls (regardless of method).

---

## 10. Phase 10: Expand Property Sources

### 10.1 Objective

Increase coverage by adding more UK property listing sources, with a focus on:

- **Mainstream Portals**: To maximize listing volume.
- **Auction Houses**: For distressed/below-market properties.
- **Specialist Sites**: Repossessions, commercial, land registries.

### 10.2 Target Sources

#### 10.2.1 Major Portals (High Volume, Likely APIs)

| Source        | Type   | Priority | API Likelihood | Notes                                                    |
| ------------- | ------ | -------- | -------------- | -------------------------------------------------------- |
| OnTheMarket   | Portal | High     | ✅ Likely      | Modern React site, likely has JSON API.                  |
| Purplebricks  | Portal | High     | ✅ Likely      | Tech-forward company, clean data structure expected.     |
| Boomin        | Portal | High     | ✅ Likely      | New portal (2021), modern stack, likely API-driven.      |
| Home.co.uk    | Portal | Medium   | ✅ Likely      | Aggregator with historical data, has known API patterns. |
| Nestoria      | Portal | Medium   | ✅ Confirmed   | Has public API (api.nestoria.co.uk).                     |
| PrimeLocation | Portal | Medium   | ✅ Likely      | Owned by Zoopla, same tech stack probable.               |
| FindaProperty | Portal | Low      | ❓ Unknown     | Older site, may lack modern API.                         |

#### 10.2.2 Auction Houses (Distressed Properties)

| Source                   | Type    | Priority | API Likelihood | Notes                                         |
| ------------------------ | ------- | -------- | -------------- | --------------------------------------------- |
| Allsop                   | Auction | High     | ❓ To Check    | Major UK auction house, mixed stock.          |
| Savills Auctions         | Auction | High     | ✅ Likely      | Large firm, modern website.                   |
| SDL Property Auctions    | Auction | High     | ❓ To Check    | One of UK's largest, handles 2000+ lots/year. |
| Network Auctions         | Auction | Medium   | ❓ To Check    | National coverage.                            |
| Auction House (Regional) | Auction | Medium   | ❓ To Check    | Multiple regional branches (already partial). |
| Barnard Marcus Auctions  | Auction | Medium   | ❓ To Check    | London & South East focus.                    |
| Clive Emson              | Auction | Medium   | ❓ To Check    | South of England specialist.                  |
| Strettons                | Auction | Low      | ❓ To Check    | London commercial & residential.              |
| Countrywide Auctions     | Auction | Low      | ❓ To Check    | Nationwide network.                           |

#### 10.2.3 Specialist & Repossession Sources

| Source                   | Type         | Priority | API Likelihood | Notes                                             |
| ------------------------ | ------------ | -------- | -------------- | ------------------------------------------------- |
| LPA Receivers            | Repossession | High     | ❓ To Check    | Direct bank repossessions.                        |
| National Asset Loan Mgmt | Repossession | High     | ❓ To Check    | NAMA - Irish but covers UK assets.                |
| Express Estate Agency    | Online Agent | Medium   | ✅ Likely      | Modern online-only agent.                         |
| YOPA                     | Online Agent | Medium   | ✅ Likely      | Hybrid online agent, tech-focused.                |
| Strike (Housesimple)     | Online Agent | Medium   | ✅ Likely      | Free online agent, modern platform.               |
| EweMove                  | Online Agent | Low      | ❓ Unknown     | Franchise model.                                  |
| HousingUnits.co.uk       | Aggregator   | Low      | ❓ To Check    | Aggregates multiple sources.                      |
| PropertyHeads            | Social       | Low      | ❓ To Check    | Property social network, private sales.           |
| TheHouseShop             | Portal       | Medium   | ❓ To Check    | Allows private sellers, may have unique listings. |

#### 10.2.4 Data & Valuation Sources (Not Listings)

| Source               | Type | Priority | API Likelihood | Notes                                    |
| -------------------- | ---- | -------- | -------------- | ---------------------------------------- |
| Gov.uk Land Registry | Data | Medium   | ✅ Confirmed   | Free Price Paid API available.           |
| Mouseprice           | Data | Low      | ❓ To Check    | Valuation estimates.                     |
| PropertyData.co.uk   | Data | Low      | ✅ Has API     | Paid API but useful for market analysis. |

### 10.3 API Investigation Priority

Based on likelihood of having accessible APIs, investigate in this order:

1. **Nestoria** - Confirmed public API (api.nestoria.co.uk)
2. **Gov.uk Land Registry** - Confirmed free API for sold prices
3. **OnTheMarket** - Modern React site, high chance of JSON endpoints
4. **Boomin** - New platform, likely clean API architecture
5. **Purplebricks** - Tech company, likely has internal APIs
6. **SDL Property Auctions** - Large volume, may have data feeds
7. **Savills Auctions** - Major firm, professional web presence

### 10.4 Tasks

- [x] **Nestoria API**: Implemented (currently disabled due to API SSL issues server-side).
- [ ] **Land Registry API**: Integrate for sold price validation/comparisons.
- [x] Implement `search_onthemarket()` method.
- [x] Implement `search_boomin()` method.
- [x] Implement `search_purplebricks()` method.
- [x] Implement `search_sdl_auctions()` method.
- [x] Implement `search_allsop()` method.
- [ ] Create a `SourceManager` class for plug-and-play source registration.
- [ ] Add source health monitoring (detect when a scraper breaks).
- [ ] Build API audit script to test each source for JSON endpoints.

---

## 11. Phase 11: Enhanced LLM Analysis & Filtering

### 11.1 Problem Statement

The current LLM integration (Ollama with Llama 3) has limitations:

- **Local-Only**: Requires users to install Ollama and download models.
- **Limited Context**: Smaller models may miss nuanced property descriptions.
- **No User Customization**: Scoring weights are hardcoded.

### 11.2 Solution: Free LLM Options Only

All LLM options must be **completely free** (no credit card required, no pay-per-use):

| Option                | Type  | Cost | Quality | Notes                                    |
| --------------------- | ----- | ---- | ------- | ---------------------------------------- |
| Ollama (Llama 3)      | Local | Free | Good    | Current implementation, requires setup.  |
| Groq API              | Cloud | Free | Great   | Generous free tier, very fast inference. |
| HuggingFace Inference | Cloud | Free | Varies  | Free tier with Serverless Inference API. |
| Google AI Studio      | Cloud | Free | Great   | Free Gemini API access (rate limited).   |

> **Requirement**: We will NOT integrate any LLM that requires payment or a credit card. The heuristic analyzer remains the default for zero-dependency operation.

**For the Web Interface**: LLM analysis happens during the GitHub Actions scrape (server-side), not in the browser. The pre-scored results are stored in JSON, so the static site doesn't need any API keys.

### 11.3 Enhanced Filtering for Web Interface

Allow users to filter and customize via the web UI:

- **Price Range**: ✅ **Implemented** - Min/Max sliders.
- **Property Type**: ✅ **Implemented** - Checkboxes (House, Flat, Land).
- **Condition Tags**: ✅ **Implemented** - Distressed, Fixer Upper, Standard.
- **Tenure**: ✅ **Implemented** - Freehold, Leasehold, Unknown filters.
- **Score Threshold**: ✅ **Implemented** - Only show properties above X score.
- **Custom Keywords**: User-defined positive/negative keywords.
- **Exclude Auctions**: ✅ **Implemented** - Quick toggle to hide all auction properties.

### 11.4 Tasks

- [ ] Integrate Groq API as a free cloud LLM option.
- [ ] Create LLM provider abstraction (`LLMProvider` interface).
- [x] Build filter panel component for web interface.
- [x] Add "Exclude All Auctions" quick filter with smart detection.
- [ ] Allow users to save filter presets.
- [ ] Implement real-time re-scoring when filters change.

---

## 12. Roadmap Summary

| Phase | Description                         | Status         |
| ----- | ----------------------------------- | -------------- |
| 1-5   | Core CLI, Scraping, Heuristics, LLM | ✅ Completed   |
| 6     | Usability Overhaul                  | ✅ Completed   |
| 7     | Source Expansion (Auctions)         | ✅ Completed   |
| 8     | Web Interface + GitHub Pages        | ✅ Completed   |
| 9     | API-First Scraping Overhaul         | 🔄 In Progress |
| 10    | Expand Property Sources             | 🔄 In Progress |
| 11    | Enhanced LLM & Filtering            | 🔲 Not Started |

---

## 13. Files Created/Modified (Phase 8-10)

### New Files

- `index.html` - Main web interface entry point
- `assets/css/style.css` - Responsive stylesheet
- `assets/js/app.js` - Frontend JavaScript application
- `data/properties.json` - Sample property data
- `src/json_exporter.py` - JSON export utility
- `scripts/scrape_for_web.py` - GitHub Actions scraper script
- `.github/workflows/scrape.yml` - Automated daily scrape workflow

### Modified Files

- `src/scraper.py` - Added `search_onthemarket()` and `search_nestoria()` methods
- `requirements.txt` - Added `httpx` dependency
- `scripts/scrape_for_web.py` - Added nationwide England search (40+ cities)
- `.github/workflows/scrape.yml` - Default changed to `england` for nationwide coverage
- `assets/js/app.js` - Added `excludeAuctions` filter and `isAuctionProperty()` detection
- `assets/css/style.css` - Added `.filter-highlight` and `.toggle-label` styles
