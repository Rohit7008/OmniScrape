# OmniScrape AI: Master Project Execution Plan

## 1. Executive Summary
**OmniScrape AI** is a lightweight, high-performance automated intelligence tool designed to aggregate the most recent data about any entity (person or company) from across the web. It bypasses the "stale data" problem of traditional LLMs by fetching live search results, scraping the content, and synthesizing a structured report using Gemini 1.5 Flash.

The project operates under a strict **Zero-Cost Architecture** by maximizing the free tiers of modern AI-native search, scraping, and LLM APIs.

---

## 2. Technical Stack & Zero-Cost Limits
To maintain the zero-cost requirement, we will strictly use the following stack and stay within their free-tier limits:

| Component | Provider | Role | Strict Free Tier Limit |
|-----------|----------|------|------------------------|
| **Search Engine** | [Tavily API](https://tavily.com/) | Finds top-ranking URLs from the last 24-48 hours. | **1,000 searches/month** (approx. 30 searches/day) |
| **Web Scraper** | [Firecrawl](https://www.firecrawl.dev/) | Bypasses anti-bot protections and extracts clean Markdown pages. | **500 credits/month** (approx. 15-20 deep scrapes/day) |
| **Intelligence/LLM** | [Gemini 1.5 Flash](https://aistudio.google.com/) | Analyzes chunked markdown, summarizes, and formats output. | **15 requests/minute** (1 million tokens/min) |
| **Environment** | Python 3.10+ | Orchestrates the entire pipeline locally. | N/A (Local) |

---

## 3. Core Workflow (The Pipeline)
1. **Input Phase:** User runs a CLI command (e.g., `python main.py --target "OpenAI" --type company`).
2. **Discovery Phase:** Script calls Tavily API with `search_depth="advanced"` and temporal filters to retrieve the top 5 most relevant URLs.
3. **Extraction Phase:** Script iterates through the URLs and passes them to Firecrawl. Firecrawl strips ads, JS bloat, and navbars, returning pure Markdown.
4. **Synthesis Phase:** The combined Markdown from all URLs is injected into a Gemini 1.5 Flash prompt instructing it to build a highly structured profile.
5. **Output Phase:** Script saves a `[target_name]_report.md` and a structured `[target_name]_data.json` locally.

---

## 4. End-to-End Phased Execution Plan

### Phase 1: Environment Setup & Foundation (Day 1)
**Goal:** Prepare the workspace, secure API keys, and define the architecture.
* **Step 1.1:** Register and generate API keys for Tavily, Firecrawl, and Google AI Studio (Gemini). Store them locally in a `.env` file.
* **Step 1.2:** Initialize a local Git repository and create the Python virtual environment (`python -m venv venv`).
* **Step 1.3:** Create the basic folder structure:
  ```text
  omniscrape-ai/
  ├── .env
  ├── .gitignore
  ├── main.py              # CLI entry point
  ├── src/
  │   ├── search.py        # Tavily integration
  │   ├── scraper.py       # Firecrawl integration
  │   ├── prompt.py        # Gemini system prompts
  │   └── synthesizer.py   # LLM orchestration
  ├── output/              # Generated reports directory
  └── requirements.txt
  ```
* **Step 1.4:** Install dependencies: `pip install firecrawl-py google-generativeai tavily-python python-dotenv textwrap3`.

### Phase 2: Building the API Connectors (Day 2)
**Goal:** Ensure we can successfully fetch recent links and extract clean text from them.
* **Step 2.1 - Search Module:** Implement `src/search.py`. Write a function `get_latest_news(query, limit=5)` using the Tavily client. It must return raw URLs and brief snippet context.
* **Step 2.2 - Scraper Module:** Implement `src/scraper.py`. Write a function `scrape_urls(urls)` using `firecrawl-py`. 
* **Step 2.3 - Error Handling:** Add `try/except` blocks to handle 403 Forbidden errors if Firecrawl gets blocked, silently falling back or skipping that specific URL to not break the pipeline.

### Phase 3: The "Brain" & Prompt Engineering (Day 3)
**Goal:** Instruct Gemini to process the scraped Markdown accurately without hallucinations.
* **Step 3.1 - Prompt Design:** Create a robust system prompt in `src/prompt.py`. The prompt must strictly enforce:
  * Extracting Executive Summary, Key Developments, Public Sentiment, and Financial/Career Signals.
  * *Crucial requirement:* **Cite the source URL** for every factual claim.
* **Step 3.2 - LLM Integration:** Implement `src/synthesizer.py`. Use the `google-generativeai` SDK. Pass the combined Markdown from Phase 2 into Gemini 1.5 Flash.
* **Step 3.3 - Token Management:** Even with Gemini's 1M+ token window, implement a safeguard to truncate scraped markdown if it exceeds safe limits (e.g., limit total characters passed to the LLM to 500k to ensure fast latency).

### Phase 4: Pipeline Integration & CLI Assembly (Day 4)
**Goal:** Tie the modules together into a seamless User Experience.
* **Step 4.1:** Build `main.py`. Import search, scraper, and synthesizer.
* **Step 4.2:** Use Python's `argparse` to allow CLI commands:
  * `python main.py --name "Deepinder Goyal"`
  * `python main.py --name "Zomato" --type company --days 7`
* **Step 4.3:** Add rich console output (using the `rich` library) to show progress spinners while API calls are running (e.g., "🔍 Searching Web...", "🕷️ Scraping Pages...", "🧠 Synthesizing Report...").
* **Step 4.4:** Write the final response to the `/output` directory as a beautifully formatted `.md` file.

### Phase 5: Guardrails, Limits, & Polishing (Day 5)
**Goal:** Ensure the system respects the zero-cost boundaries and doesn't crash on edge cases.
* **Step 5.1:** Implement **Rate Limit Pauses**. Add `time.sleep(3)` between Firecrawl scraper requests to avoid hitting concurrent execution limits on the free tier.
* **Step 5.2:** Add ethical guardrails in code. Example: Hardcode a ban-list of domains (e.g., `['login.', 'auth.', 'bank.']`) in `search.py` so we don't waste Firecrawl credits on pages we know require login.
* **Step 5.3:** Final end-to-end testing with 5 different entity types (e.g., a startup, a public CEO, an obscure library, a crypto project). Review the output accuracy.

---

## 5. Potential Bottlenecks & Solutions

1. **Firecrawl Monthly Credit Exhaustion:** The tightest limit is Firecrawl (500 credits). 
   * *Solution:* Limit the pipeline to scraping only the top **3 URLs** per query instead of 10. For less important URLs, fallback to simply using Tavily's standard snippet summary (`search_depth="basic"`) which costs nothing to scrape.
2. **Sites Blocking Scrapers (403/Captchas):**
   * *Solution:* Firecrawl is built to bypass most, but if it fails, the script should gracefully catch the error, log a warning, and proceed to synthesize using whatever data it *did* successfully fetch.
3. **Gemini Free Tier API Pauses:**
   * *Solution:* Limit requests strictly and enforce retries using exponential backoff if a `429 Too Many Requests` error hits Google AI Studio.

---

## 6. Next Actions Required to Start Execution

1. **Create the `.env` file** in this directory and populate with:
   ```env
   TAVILY_API_KEY="your_tavily_key"
   FIRECRAWL_API_KEY="your_firecrawl_key"
   GEMINI_API_KEY="your_gemini_key"
   ```
2. **Run Environment Setup** commands.
3. Once keys are ready, we can immediately begin writing the code for **Phase 1** and **Phase 2**. 

*Let me know when you are ready to generate the actual Python code module by module!*
