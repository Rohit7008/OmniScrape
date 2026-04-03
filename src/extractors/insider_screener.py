"""
Module to scrape InsiderScreener and extract top-of-funnel HNI leads.
"""
import time
import json
import re
from rich.console import Console
from playwright.sync_api import sync_playwright
import google.generativeai as genai
from src.synthesizer import init_gemini

console = Console()

def get_insider_screener_deals(limit=None) -> list[dict]:
    """Scrapes InsiderScreener.com (India) for recent insider trades."""
    url = "https://www.insiderscreener.com/en/explore/in"
    console.print(f"\n[cyan]Starting Playwright execution for InsiderScreener: {url}[/cyan]")
    
    extracted_texts = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # Give it a few seconds to load dynamic data
            page.wait_for_timeout(3000)
            
            # Extract main page text
            main_text = page.evaluate("() => document.body.innerText")
            extracted_texts.append(f"--- MAIN LIST PAGE ---\n{main_text[:25000]}") # Grab a massive chunk of the body
            
            # Get detail links for companies to get aggregated data
            js_script_companies = '''() => {
                let links = Array.from(document.querySelectorAll("a[href*='/en/company/']"));
                let unique = [...new Set(links.map(a => a.href))];
                return LIMIT_PLACEHOLDER ? unique.slice(0, LIMIT_PLACEHOLDER) : unique;
            }'''.replace("LIMIT_PLACEHOLDER", str(limit) if limit else "null")
            company_links = page.evaluate(js_script_companies)
            
            # Get direct transactor profile links
            js_script_insiders = '''() => {
                let links = Array.from(document.querySelectorAll("a[href*='/en/insider/']"));
                let unique = [...new Set(links.map(a => a.href))];
                return LIMIT_PLACEHOLDER ? unique.slice(0, LIMIT_PLACEHOLDER) : unique;
            }'''.replace("LIMIT_PLACEHOLDER", str(limit) if limit else "null")
            main_insider_links = page.evaluate(js_script_insiders)
            
            console.print(f"[green]Found {len(company_links)} company detail links and {len(main_insider_links)} transactor profile links on root list...[/green]")
            
            all_insider_links = set(main_insider_links)
            
            # Visit each detail page
            for link in company_links:
                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)
                    detail_text = page.evaluate("() => document.body.innerText")
                    extracted_texts.append(f"--- COMPANY DETAIL {link} ---\n{detail_text[:15000]}")
                    
                    # Extract top 3 insider links from this company page to chain scrape
                    insider_links = page.evaluate('''() => {
                        let links = Array.from(document.querySelectorAll("a[href*='/en/insider/']"));
                        let unique = [...new Set(links.map(a => a.href))];
                        return unique.slice(0, 3);
                    }''')
                    for i_link in insider_links:
                        all_insider_links.add(i_link)
                except Exception as e:
                    console.print(f"[yellow]Failed to load detail page {link}: {e}[/yellow]")
            
            # Phase 3: Traversal of deduplicated Insider Profile Links
            console.print(f"[green]Found {len(all_insider_links)} unique insider profiles to chain scrape...[/green]")
            for link in all_insider_links:
                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)
                    profile_text = page.evaluate("() => document.body.innerText")
                    extracted_texts.append(f"--- INSIDER PROFILE {link} ---\n{profile_text[:15000]}")
                except Exception as e:
                    console.print(f"[yellow]Failed to load insider profile {link}: {e}[/yellow]")
            
        except Exception as e:
            console.print(f"[red]Error during Playwright navigation:[/red] {e}")
            browser.close()
            return []
        
        browser.close()
            
    combined_text = "\n\n".join(extracted_texts)
    
    if not extracted_texts:
        console.print("[red]No text extracted from InsiderScreener.[/red]")
        return []
        
    console.print(f"[green]Successfully grabbed {len(combined_text)} characters of text! Analyzing for insider liquidity events...[/green]")
    
    init_gemini()
    
    limit_text = f"up to {limit} people" if limit else "ALL available individuals"
    prompt = f"""
You are a financial data parser. I am giving you the raw text scraped from the InsiderScreener website (Main list + Company Detail pages + Insider Profile pages).

CRITICAL INSTRUCTION: Extract TWO groups of people:
1. Daily Transactors (from the main list page).
2. Top Investors (from the Company Detail pages).

Extract {limit_text} from these combined groups. For EVERY person extracted, you MUST scan the Insider Profile data and explicitly extract their network connections into a separate `network_context` field (e.g., "Director at [Company A], Promoter at [Company B]"). If no other companies exist, leave `network_context` empty.

Do NOT extract generic corporate entities unless they represent a family office. Prioritize human names.

Return strictly a valid JSON array of objects. Each object must have:
"source": "InsiderScreener",
"name": (The name of the Insider, Title Case),
"deal_date": "DD/MM/YYYY" (or "Top Investor History" if they didn't explicitly transact today),
"deal_type": "Buy", "Sell", or "Top Investor Hold",
"quantity": "[Premium Required]",
"price": "[Premium Required]",
"deal_context": "Company: [Company], Sector: [Sector], 90d Net Buy/Sell: [Value], Position: [Insider Position]",
"network_context": "Additional companies/commitments extracted from the Insider Profile"

Example:
[
  {{"source": "InsiderScreener", "name": "Rahul Bajaj", "deal_date": "20/03/2026", "deal_type": "Buy", "quantity": "[Premium Required]", "price": "[Premium Required]", "deal_context": "Company: Bajaj Auto, Sector: Automotive, 90d Net Buy: 50Cr INR, Position: Promoter", "network_context": "Chairman at Bajaj Finance, Director at Mukand Ltd"}}
]
If none exist, return []

DATA:
{combined_text[:500000]}
"""
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
    )
    
    res = None
    for attempt in range(3):
        try:
            res = model.generate_content(prompt)
            break
        except Exception as e:
            if "429" in str(e):
                console.print(f"[yellow]Quota limit hit (429). Waiting 35s... (Attempt {attempt+1}/3)[/yellow]")
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
