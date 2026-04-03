# OmniScrape AI - Project Analysis

## 1. Project Aim
**OmniScrape AI** is a lightweight, high-performance automated intelligence tool designed to aggregate the most recent data about any entity (person or company) from across the web. Primarily, it is tailored to serve as an automated **High Net-worth Individual (HNI) Lead Sourcing pipeline**. It tracks recent liquidity events (wealth generation events) and builds detailed, actionable lead profiles for wealth management purposes.

## 2. Problem Solved
Traditional wealth management prospecting is highly manual, relying on manually scanning stock exchange deals, news sites, and corporate registries. Furthermore, traditional LLMs suffer from "stale data" issues because their training cuts off at a certain date. 

OmniScrape solves these problems by:
- **Automating Signal Detection:** Automatically monitoring bulk deals and insider disclosures on stock exchanges (BSE, NSE, InsiderScreener).
- **Providing Real-Time Intelligence:** Fetching live search results rather than relying on an LLM's outdated internal data.
- **Cost Efficiency:** Operating under a strict **Zero-Cost Architecture** by maximizing free-tier APIs of modern search, scraping, and LLM tools.

## 3. How It Works - The Phased Approach

### Phase 1: Multi-Source Base Triage & Database Sync
- **Goal:** Detect recent liquidity events across markets that indicate a potential new HNI target.
- **Process:** The tool executes API calls to specialized extractors (`src/extractors/bse_direct.py`, `src/extractors/nse_direct.py`, and `src/extractors/insider_screener.py`). It specifically searches for large bulk deals, block deals, and insider disclosures (e.g., promoter selloffs) representing high monetary quantum.
- **Database Sync:** The extracted target leads are then filtered against the existing records cache to prevent duplicates. New records are simultaneously appended to a centralized Google Sheet (using `src/sheets.py`) with their base transaction metadata (Name, Deal Date, Quantity, Price, Context). Their processing status is marked as "Pending".

### Phase 2: OmniScrape Deep Profile Extraction
- **Goal:** Unearth comprehensive internet-wide intelligence for the pending leads gathered in Phase 1.
- **Process:** It retrieves the "Pending" target records from the Google Sheet (often limiting batch processing to just a couple records to save AI limits). For each target, the script invokes the Tavily API, passing the entity name and known liquidity context to fetch top-ranking web URLs (covering the last 24-48 hours). The Firecrawl tool then deeply scrapes these URLs, intentionally bypassing bot-protections and JS bloat to aggregate clean Markdown text.
- **Synthesis:** All stripped Markdown files are sent into a rigid system prompt via Google's Gemini 1.5/2.5 Flash API (`src/prompt.py`) built directly for wealth management intelligence mapping. 
- **Database Update:** The LLM strictly structures the findings into JSON format. Finally, `src/sheets.py` targets the distinct Google Sheet row created in Phase 1, merges all the deep intelligence variables, and shifts the status to "Done". A structured human-readable Markdown file (`output/[target_name]_report.md`) is safely written to the active disk as well.

## 4. Database Schema & Saved Fields
All insights tracked across Phase 1 and Phase 2 are continuously updated to a single unified Google Sheet acting as the Central Database. The mapped fields include:

1. **Source:** Data origin of the target (e.g., BSE, NSE, InsiderScreener).
2. **Target Name:** Target's Name or Entity identifier.
3. **Deal Date:** Date of initial liquidity event execution.
4. **Deal Type:** Deal execution category (e.g., Block Deal, Bulk Deal).
5. **Quantity:** Volume of shares linked to the transaction.
6. **Price:** The execution price per share/unit of the transaction.
7. **Liquidity Event Description:** AI-processed contextual description of the exact secondary sale, block deal, or M&A generating vast liquidity.
8. **Estimated Quantum (₹):** The total financial valuation calculated from the actual sale event (Quantity * Price).
9. **Active Companies / Directorships:** A cross-referenced list of active corporate roles, companies controlled, or DIN/CIN structures found across websites, Tofler, or Zauba Corp mentions.
10. **Financial Health (Revenue/Capital):** Scraped overarching financial parameters, revenue, or net worth associated with target entities.
11. **Warm Intro Paths (Lawyers/CAs):** High-value network mapping specifying referencing lawyers, wealth firms, M&A advisors, or CA firms who were involved in their recent deals.
12. **Profile Notes / Philanthropy:** Captured highlights detailing general tone, known family office involvements, and philanthropic contributions found online.
13. **Source Verification Links:** Source citations referencing the raw news URLs/indexes Gemini extracted the intelligence from.
14. **Date Added:** Origin timestamp the target was identified into the architecture.
15. **Status:** Processing step ("Pending" vs "Done").
16. **Phase 1 Timestamp:** Granular timestamp mapping exact time of Base Triage completion.
17. **Phase 2 Timestamp:** Granular timestamp mapping exact time of Deep Extraction & Google sheet update.

## 5. Technicalities
- **Programming Language:** Python 3.10+
- **Pipeline Orchestration:** Local Python script with a CLI (`main.py`) powered by `argparse` and `rich` for terminal UI.
- **APIs and Services:**
  - **Search:** [Tavily API] (Extracts contextual URLs).
  - **Scraping:** [Firecrawl] (Deep extracts pure Markdown).
  - **Intelligence:** [Google Gemini 1.5/2.5 Flash] (Contextual processing and JSON/Markdown generation).
  - **Storage:** Google Sheets API (`src/sheets.py`).
- **Core Modules:**
  - `src/search.py`: Integrates Tavily for finding relevant URLs.
  - `src/scraper.py`: Integrates Firecrawl to bypass rate limits and fetch markdown.
  - `src/synthesizer.py`: Connects to Gemini for information extraction.
  - `src/extractors/`: Specific scrapers for BSE, NSE, and InsiderScreener.

## 6. Inputs
The pipeline supports two operational modes through the CLI:
- **Standard Mode:** 
  - `--name`: Name of the target person or company (e.g., "Deepinder Goyal").
  - `--type`: Type of entity (`person` or `company`).
  - `--limit`: Max number of deep URLs to scrape per run.
- **HNI Sourcing Mode:**
  - `--mode hni_sourcing`: Automates the entire Phase 1 & Phase 2 workflow.
  - `--source`: Specifies which feed to scrape for new targets (`all`, `bse`, `nse`, `insider_screener`).
  - Fetches the "pending queue" of targets automatically from a connected Google Sheet.

## 7. Outputs & Results
For every successful pipeline run, the system outputs:
1. **Google Sheets Refresh:** An immediate, real-time sync mapping heavily enriched network parameters onto tracking targets. 
2. **Local Markdown Report:** A beautifully structured `.md` offline profile detailing Executive Summary, Public Sentiment, and Financial signals.
3. **Structured JSON:** Core system variables saved as `[target_name]_fallback.json` (or processed dynamically mid-air).
4. **Command-Line Feedback:** Live-terminal visual progression marking the status of parsing, scraping, and Google Sheet syncs.
