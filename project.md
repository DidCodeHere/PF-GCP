# Project White Paper: Smart Property Finder CLI

## 1. Executive Summary
The **Smart Property Finder CLI** is a terminal-based tool designed for construction companies and property investors. Its primary mission is to automate the discovery of high-potential, low-cost investment opportunities in the UK property market. Specifically, it targets freehold properties (flats, houses, land) under £100,000 that require renovation or development.

By leveraging web scraping technologies and local Artificial Intelligence (AI), the system identifies properties that traditional filters might miss, focusing on description analysis to find "fixer-uppers" and development deals.

## 2. Work Done
- [x] **Project Initialization**: Established repository structure and version control.
- [x] **Requirements Definition**: Outlined core features, target platforms, and AI integration strategy.
- [ ] **Scraper Implementation**: (Pending) Development of robust scraping modules for Rightmove and Zoopla using browser automation.
- [ ] **AI Analyzer Engine**: (Pending) Integration of a free, open-source local LLM to score properties based on renovation potential.
- [ ] **CLI Interface**: (Pending) specific command-line entry points for user interaction.

## 3. Feature Requirements

### 3.1. Core Functionality
- **Search Capabilities**:
    - Input: Location (Postcode or Town) and Search Radius (miles).
    - Filters: Max Price (£100,000), Tenure (Freehold), Property Type (Houses, Flats, Land).
- **Data Acquisition (Scraping)**:
    - Must handle dynamic HTML content (Single Page Applications).
    - Resilience against basic anti-scraping measures (User-Agent rotation, rate limiting).
    - Extract: Price, Address, Description, Agent Link, Tenure.

### 3.2. AI & Smart Analysis
- **Model Selection**: Use a lightweight, open-source model (e.g., Llama 3 via Ollama, or GPT4All) to run locally without API costs.
- **Analysis Logic**:
    - Analyze property descriptions for keywords and sentiment indicating "renovation required", "modernisation", "refurbishment", "potential to extend", or "development land".
    - Assign an "Investment Score" (0-10) based on these factors.
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
1.  **Phase 1**: Build the scraper for Rightmove (most popular).
2.  **Phase 2**: Implement keyword-based scoring (heuristic).
3.  **Phase 3**: Integrate Local LLM for semantic analysis.
4.  **Phase 4**: Add Zoopla support and export features.
