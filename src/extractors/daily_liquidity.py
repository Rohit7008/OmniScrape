"""
Module for hunting new liquidity events using the allowed PDF news sources (Idea 1).
"""
import json
import google.generativeai as genai
from rich.console import Console

from src.search import init_tavily
from src.synthesizer import init_gemini

console = Console()

def find_new_hnis_today() -> list[str]:
    """
    Searches the allowed financial news websites for recently reported bulk deals,
    block deals, or startup funding, then uses Gemini to extract the names.
    Returns: A list of string names (e.g., ["Deepinder Goyal", "Bhavish Aggarwal"]).
    """
    client = init_tavily()
    
    # Query constrained to specific PDF sources
    query = '("promoter" OR "founder") AND ("bulk deal" OR "block deal" OR "stake sale" OR "funding")'
    sites = '(site:economictimes.indiatimes.com OR site:business-standard.com OR site:livemint.com OR site:inc42.com OR site:bseindia.com)'
    
    console.print("[cyan]Hunting for historical liquidity events on PDF Sources...[/cyan]")
    response = client.search(
        query=f"{query} {sites}",
        search_depth="advanced",
        max_results=10,
        topic="general"
    )
    
    results = response.get("results", [])
    if not results:
        return []
        
    snippets = []
    for r in results:
        snippets.append(f"Title: {r.get('title')}\nContent: {r.get('content')}")
        
    combined_feed = "\n---\n".join(snippets)
    
    # Interrogate the snippets using Gemini purely to extract human names
    init_gemini()
    
    prompt = f"""
You are an expert financial analyst. Read the following news snippets about recent stock market bulk deals and startup funding rounds in India.
Your goal is to extract the names of the INDIVIDUALS (founders, promoters, or executives) who recently sold shares or raised significant funding.
Do NOT list company names. ONLY list the human names. 
If there are multiple people, list them all.
Return the result strictly as a valid JSON array of strings. For example: ["Ratan Tata", "Kunal Bahl"]
If no human names are distinctly mentioned as selling/raising, return an empty array: []

SNIPPETS:
{combined_feed}
"""
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
    )
    
    try:
        res = model.generate_content(prompt)
        names = json.loads(res.text)
        if isinstance(names, list):
            # Clean up names
            return [str(n).strip() for n in names if n]
        return []
    except Exception as e:
        console.print(f"[red]Error parsing names from LLM:[/red] {e}")
        return []
