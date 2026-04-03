"""
Module for fetching URLs via Tavily API
"""
import os
from tavily import TavilyClient
from rich.console import Console

console = Console()

def init_tavily():
    """Initialize Tavily Client."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key == "your_tavily_key":
        raise ValueError("Missing TAVILY_API_KEY in .env")
    return TavilyClient(api_key=api_key)

def is_allowed_url(url: str) -> bool:
    """Check if URL contains blocked subdomains or paths to save scraper credits."""
    blocked_fragments = [
        "login", "auth", "signin", "signup", "bank",
        "myaccount", "dashboard", "portal"
    ]
    for fragment in blocked_fragments:
        if fragment in url.lower():
            return False
    return True

def get_latest_news(query: str, days: int = 7, limit: int = 5) -> list[dict]:
    """
    Search the web for the latest deep links about the query.
    Returns a list of dicts with 'url', 'title', 'content'.
    """
    client = init_tavily()
    
    # Fetch extra to account for discarded URLs
    search_query = f"{query} recent news updates"
    
    response = client.search(
        query=search_query,
        search_depth="advanced",
        max_results=limit * 2,
        topic="general"
    )
    
    results = []
    for item in response.get("results", []):
        url = item.get("url", "")
        if is_allowed_url(url):
            results.append({
                "url": url,
                "title": item.get("title", ""),
                "content": item.get("content", "") # basic snippet as a fallback
            })
        
        if len(results) >= limit:
            break
            
    return results

def get_hni_news(query: str, limit: int = 5, deal_context: str = "") -> list[dict]:
    """
    Search the global web for HNI specific profiles.
    """
    client = init_tavily()
    
    # Extract the company name from the deal context to sharpen the search
    context_hint = ""
    if deal_context:
        words = deal_context.split()
        if "of" in words:
            try:
                context_hint = words[words.index("of") + 1]
            except Exception:
                pass
                
    # 1. Mandatory Domains Search - Split queries to enforce hits across ALL sources
    mandatory_query = f'"{query}"'
    if context_hint:
        mandatory_query = f'"{query}" OR "{context_hint}"'
        
    mandatory_domains = ["zaubacorp.com", "tofler.in", "crunchbase.com", "economictimes.indiatimes.com", "livemint.com", "business-standard.com"]
    response_mandatory = []
    
    for domain in mandatory_domains:
        try:
            res = client.search(
                query=mandatory_query,
                search_depth="advanced",
                include_domains=[domain],
                max_results=2, # Grab top 2 per domain guarantees diversity
                topic="general"
            )
            domain_results = res.get("results", [])
            if not domain_results:
                console.print(f"[yellow]  - No results found in {domain}[/yellow]")
            response_mandatory.extend(domain_results)
        except Exception as e:
            console.print(f"[yellow]  - No results found in {domain} (Search Error)[/yellow]")
        
    # 2. General Web Search (Unrestricted open web)
    if context_hint:
        search_query = f'"{query}" AND ("{context_hint}" OR director OR founder OR invest) -filetype:pdf'
    else:
        search_query = f'"{query}" AND (director OR founder OR net worth) -filetype:pdf'
    
    try:
        response_general = client.search(
            query=search_query,
            search_depth="advanced",
            max_results=max(limit, 5),
            topic="general",
            exclude_domains=["instagram.com", "facebook.com", "youtube.com"] + mandatory_domains
        )
    except Exception as e:
        response_general = {"results": []}
    
    results = []
    
    # Prioritize ALL mandatory results
    for item in response_mandatory:
        url = item.get("url", "")
        if ".pdf" not in url.lower() and url not in [r["url"] for r in results]:
            results.append({
                "url": url,
                "title": item.get("title", ""),
                "content": item.get("content", "")
            })
            
    # Add general results up to limit
    general_added = 0
    for item in response_general.get("results", []):
        url = item.get("url", "")
        # Prevent duplicates overall
        if ".pdf" not in url.lower() and url not in [r["url"] for r in results]:
            results.append({
                "url": url,
                "title": item.get("title", ""),
                "content": item.get("content", "")
            })
            general_added += 1
            if general_added >= limit:
                break
        
    return results
