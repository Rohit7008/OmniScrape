"""
Module to directly scrape the NSE Bulk Deals page and extract High Net-Worth Individual names.
"""
import json
import re
import google.generativeai as genai
from rich.console import Console

from src.scraper import init_firecrawl
from src.synthesizer import init_gemini

console = Console()

def get_nse_bulk_deal_names() -> list[str]:
    """Scrapes the live NSE bulk deals table to find individual human names."""
    app = init_firecrawl()
    url = "https://www.nseindia.com/report-detail/display-bulk-and-block-deals"
    
    console.print(f"\n[cyan]Directly scraping raw NSE Table: {url}[/cyan]")
    try:
        result = app.scrape(url)
        markdown_data = ""
        
        if hasattr(result, 'markdown') and result.markdown:
            markdown_data = result.markdown
        elif isinstance(result, dict):
            if 'data' in result and isinstance(result['data'], dict):
                markdown_data = result['data'].get("markdown", "")
            elif 'markdown' in result:
                markdown_data = result.get('markdown', '')
                
        if not markdown_data:
            console.print("[red]Could not retrieve markdown from NSE. Bot might be blocked.[/red]")
            return []
            
        console.print(f"[green]Successfully grabbed {len(markdown_data)} characters of NSE table data![/green] Analyzing for human entities...")
        
        init_gemini()
        
        prompt = f"""
You are a financial data parser. I am giving you the raw markdown scrape of the NSE Bulk Deals table.

CRITICAL INSTRUCTION: Extract EVERY SINGLE human name of the individuals listed under the "Client Name" column who sold or bought significant shares. Do not truncate! Do not summarize! Treat this as a crucial data extraction task where every person matters.

DO NOT include corporate entities, investment funds, banks, LLPs, or 'LIMITED' companies. Only real individual people/promoters.

Return strictly a valid JSON array of objects. Each object must have:
"source": "NSE",
"name": (title case), 
"deal_date": (string), 
"deal_type": (Buy or Sell), 
"quantity": (string), 
"price": (string), 
"deal_context": (a readable string combining the facts, e.g. 'Bought 1,000 shares of ALMONDZ at 13.45 INR on NSE')

If none exist, return []

DATA:
{markdown_data[:400000]}
"""
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
        )
        
        # Retry loop for 429 quota limits
        res = None
        for attempt in range(3):
            try:
                res = model.generate_content(prompt)
                break
            except Exception as e:
                if "429" in str(e):
                    console.print(f"[yellow]Quota limit hit (429). Waiting 35s... (Attempt {attempt+1}/3)[/yellow]")
                    import time
                    time.sleep(35)
                else:
                    raise e
                    
        if not res:
            return []

        try:
            deals = json.loads(res.text)
        except json.decoder.JSONDecodeError:
            console.print("[yellow]JSON Truncated! Engaging fallback emergency parser...[/yellow]")
            matches = re.findall(r'\{.*?\}', res.text, re.DOTALL)
            deals = []
            for m in matches:
                try:
                    deals.append(json.loads(m))
                except:
                    pass
        
        if isinstance(deals, list):
            return deals
        return []
        
    except Exception as e:
        console.print(f"[red]Error parsing NSE Deals:[/red] {e}")
        return []
