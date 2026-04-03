"""
Module for extracting Stage 3 Wealth Estimation data from ET Wealth.
"""
import json
import google.generativeai as genai
from rich.console import Console

from src.search import init_tavily
from src.synthesizer import init_gemini

console = Console()

def estimate_wealth_et_wealth(name: str) -> dict:
    """
    Searches ET Wealth for mentions of the target's wealth, net worth, 
    wealth managers, or investment philosophy.
    Returns: A dictionary with extracted wealth context.
    """
    client = init_tavily()
    
    # Restrict to ET Wealth domain
    query = f'"{name}" (net worth OR wealth OR investment OR family office)'
    site_filter = "site:economictimes.indiatimes.com/wealth"
    
    console.print(f"[cyan]Searching ET Wealth for wealth context on: {name}[/cyan]")
    response = client.search(
        query=f"{query} {site_filter}",
        search_depth="advanced",
        max_results=5,
        topic="general"
    )
    
    results = response.get("results", [])
    if not results:
        console.print(f"[yellow]No ET Wealth articles found for {name}.[/yellow]")
        return {"source": "ET Wealth", "name": name, "wealth_summary": "No data found", "key_findings": [], "articles": []}
        
    snippets = []
    articles = []
    for r in results:
        snippets.append(f"Title: {r.get('title')}\nContent: {r.get('content')}")
        articles.append(r.get("url"))
        
    combined_feed = "\n---\n".join(snippets)
    
    init_gemini()
    
    prompt = f"""
You are an expert wealth intelligence analyst. Review the following news snippets from ET Wealth about the individual named '{name}'.
Your goal is to extract any information related to their wealth quantum, net worth, wealth management approach, family office, or recent major liquidity events.
Do not hallucinate. If there is no relevant wealth information in these snippets, explicitly state that.

Return the result strictly as a valid JSON object with the following structure:
{{
  "source": "ET Wealth",
  "name": "{name}",
  "wealth_summary": "A concise paragraph summarizing their known wealth context based on the snippets",
  "key_findings": ["Bullet point 1", "Bullet point 2"]
}}

SNIPPETS:
{combined_feed}
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
                console.print(f"[yellow]ET Wealth hit Quota limit (429). Waiting 35s... (Attempt {attempt+1}/3)[/yellow]")
                import time
                time.sleep(35)
            else:
                raise e
    
    if not res:
        return {"source": "ET Wealth", "name": name, "wealth_summary": "Quota limit reached", "key_findings": [], "articles": articles}

    try:
        data = json.loads(res.text)
        data["articles"] = articles
        return data
    except Exception as e:
        console.print(f"[red]Error parsing ET Wealth LLM response:[/red] {e}")
        return {"source": "ET Wealth", "name": name, "wealth_summary": "Error parsing data", "key_findings": [], "articles": articles}
