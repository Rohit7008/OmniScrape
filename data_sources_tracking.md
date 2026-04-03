# OmniScrape AI Data Integration Tracker

This tracker maps every tool, data source, and API endpoint currently active and fully integrated into the OmniScrape Pipeline.

| Stage / Phase | Name / Source Tool | URL / Endpoint | Status / Target Role | Action Flow / Integration Note |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1 (Phase 1)** | BSE Bulk Deals | `bseindia.com/markets/equity/EQReports/bulk_deals.aspx` | Active (`bse_direct.py`) | Pulls daily deals and natively tags Source: BSE |
| **Stage 1 (Phase 1)** | NSE Block Deals | `nseindia.com/report-detail/display-bulk-and-block-deals` | Active (`nse_direct.py`) | Pulls daily block deals and natively tags Source: NSE |
| **Stage 1 (Phase 1)** | InsiderScreener | `insiderscreener.com/en/explore/in` | Active (`insider_screener.py`) | Pulls recent insider stock transactions with detail aggregation |
| **Stage 2 (Phase 2)** | ZaubaCorp | `zaubacorp.com` | Active (Tavily AI) | Profiling director networks & companies |
| **Stage 2 (Phase 2)** | Tofler | `tofler.in` | Active (Tavily AI) | Extracting corporate structures & capital |
| **Stage 3 (Phase 3)** | ET Wealth | `economictimes.indiatimes.com/wealth` | Active (`et_wealth.py` / Tavily AI) | Natively scraping for Wealth Quantum/Family Office context |
| **Stage 3 (Phase 3)** | Mint | `livemint.com` | Active (Tavily AI) | M&A context, deal advisors & family office signals |
| **Stage 3 (Phase 3)** | Business Standard | `business-standard.com` | Active (Tavily AI) | Board-level changes, acquisitions & regulatory filings |
