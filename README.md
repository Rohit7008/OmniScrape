# 🌐 OmniScrape AI
**Automated Web Intelligence & HNI Lead Sourcing Pipeline**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Gemini](https://img.shields.io/badge/Google-Gemini%20Flash-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**OmniScrape AI** is a lightweight, high-performance automated intelligence tool designed to aggregate the most recent data about any entity (person or company) from across the web. Primarily functioning as an **Automated HNI Lead Sourcing Pipeline**, it tracks recent liquidity events and dynamically builds actionable, highly-structured lead profiles using AI.

By leveraging cross-web searches and deep LLM extraction, OmniScrape completely solves the traditional "stale data" bottleneck inherent in standard LLMs.

---

## ✨ Key Features
- **Zero-Cost Architecture**: Operates entirely within the free tiers of carefully selected modern AI and scraping APIs.
- **Multi-Source Signal Triage**: Automatically scrapes and discovers daily High Net-worth parameters directly from BSE Bulk Deals, NSE Block Deals, and InsiderScreener disclosures.
- **Real-Time Context Discovery**: Harnesses the Tavily internet search API to fetch the most relevant and up-to-date conversational contexts across the web.
- **Anti-Bot Deep Extraction**: Utilizes Firecrawl to systematically bypass JS-bloat, ads, and anti-scraping walls, producing clean Markdown files spanning top search results.
- **Gemini LLM Processing**: Enforces rigid prompt architectures inside Gemini 2.5 Flash to automatically interpret financial health, philanthropic paths, and wealth matrices from raw text.
- **Automated Database Sync**: Instantly logs tracked statuses, intelligence data, and warm-intro mapping straight into a centralized Google Sheet.

---

## 🚀 Architecture & Pipeline

OmniScrape AI operates through two fundamental phases designed to optimize rate-limiting while providing extremely wide sector coverage:

### Phase 1: Base Triage & Database Sync
1. Scrapers boot up to check financial boards (e.g., BSE, NSE) for large liquidity events (promoter sell-offs, bulk deals).
2. It deduplicates and cross-verifies these identities against an internal caching state.
3. Detected signals are added into a Google Sheet database as **"Pending"** leads natively containing their transaction's context.

### Phase 2: OmniScrape Deep Profile Extraction
1. Script systematically retrieves "Pending" batches from the Google Sheet.
2. It launches contextual internet searches dynamically incorporating their base liquidity event.
3. Deep markdown scraping triggers across the best web footprints.
4. Gemini Flash identifies their professional network, accountants, or associated corporate structures.
5. Google Sheet row is updated with full intelligence parameters and changed heavily enriched formats are stored locally & on cloud.

---

## 🛠 Getting Started

### 1. Prerequisites
Ensure you have Python 3.10+ installed and the following API Keys:
- **Tavily API Key**: Web Search
- **Firecrawl API Key**: Markdown Extraction
- **Google Gemini API Key**: Synthesis
- **Google Service Account JSON**: Google Sheets Connection (Optional but Recommended)

### 2. Installations
```bash
# Clone the repository
git clone https://github.com/your-username/omniscrape-ai.git
cd omniscrape-ai

# Initialize virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Create a file strictly named `.env` in the root folder bridging your config:
```env
# AI Providers
TAVILY_API_KEY="your_tavily_key"
FIRECRAWL_API_KEY="your_firecrawl_key"
GEMINI_API_KEY="your_gemini_key"

# Database Synchronization
GOOGLE_CLIENT_EMAIL="your-service-account@...iam.gserviceaccount.com"
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
GOOGLE_SHEETS_ID="sheet_id_from_url"
```

---

## 🖥 Usage

OmniScrape functions in two dynamic modes: Standard Sandbox and HNI Triage Pipelines.

### Standard Execution (Entity Search)
Search out deep intelligence manually for any query.
```bash
python main.py --name "Deepinder Goyal" --type person --limit 3
python main.py --name "OpenAI" --type company 
```

### Automated Processing (HNI Sourcing Mode)
Automatically sweeps exchanges and feeds your Google Sheets dataset. Run this daily.
```bash
python main.py --mode hni_sourcing --source all
```

**Targeted Scrapers allowed in HNI Mode:**
- `--source all`
- `--source bse`
- `--source nse`
- `--source insider_screener`

---

## 📊 Outputs & Logging 
- **Google Sheets**: A dynamically filled array containing 17 tracking variables encompassing target liquidity mappings and network insights.
- **Local Markdown Reports**: Highly readable intelligence briefs pushed securely to the `/output` local folder.
- **Robust Debug Logs**: All executions, extraction errors, and failed web nodes automatically log against `omniscrape.log` bypassing console bloat ensuring a perfectly traceable workflow.

> **Note:** The `output/`, `logs/`, and your `.env` variables are completely `.gitignore` locked to protect all proprietary extracted data configurations from being pushed to public repositories!
