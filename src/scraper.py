"""
Module for scraping deep web pages into Markdown using Firecrawl
"""
import os
import time
from rich.console import Console
from firecrawl import FirecrawlApp

console = Console()

def init_firecrawl():
    """Initialize Firecrawl Client."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key or api_key == "your_firecrawl_key":
        raise ValueError("Missing FIRECRAWL_API_KEY in .env")
    return FirecrawlApp(api_key=api_key)

def scrape_urls(urls: list[str]) -> list[dict]:
    """
    Iterates through URLs and returns clean markdown.
    Args:
        urls: A list of dicts with 'url', 'title', 'content'. Or standard string list.
    """
    app = init_firecrawl()
    scraped_data = []
    
    for item in urls:
        # It could be a string or a dict from the search module.
        url = item.get("url") if isinstance(item, dict) else item
        title = item.get("title", "No Title") if isinstance(item, dict) else url
        fallback_content = item.get("content", "") if isinstance(item, dict) else ""
        
        if not url:
            continue
            
        # QUOTA PROTECTION: Firecrawl bills 1 credit *PER PAGE* of a PDF. A 200 page PDF costs 200 credits.
        # It also fails and charges for LinkedIn/Meta due to anti-bot walls.
        if any(blocked in url.lower() for blocked in [".pdf", "linkedin.com", "instagram.com", "facebook.com", "twitter.com"]):
            console.print(f"[yellow]Harvesting Search Engine Snapshot for blocked Domain:[/yellow] {url}")
            scraped_data.append({
                "url": url,
                "title": title,
                "markdown": fallback_content # Give the AI whatever text Tavily found without invoking the scraper
            })
            continue
            
        console.print(f"[cyan]Scraping ({title}):[/cyan] {url}")
        
        try:
            # Respect free tier rate limits
            time.sleep(3)
            
            # Firecrawl v2 API uses .scrape() and returns a Document object
            result = app.scrape(url)
            
            # Different versions of firecrawl return differently. Safely extract markdown.
            markdown_content = ""
            if hasattr(result, 'markdown') and result.markdown:
                markdown_content = result.markdown
            elif isinstance(result, dict):
                # Format: {'success': True, 'data': {'markdown': '...'}}
                if 'data' in result and isinstance(result['data'], dict):
                    markdown_content = result['data'].get("markdown", "")
                elif 'markdown' in result:
                    markdown_content = result.get('markdown', '')
            
            if markdown_content:
                scraped_data.append({
                    "url": url,
                    "title": title,
                    "markdown": markdown_content
                })
                # Show success without flooding the console
                char_count = len(markdown_content)
                console.print(f"[green]Success![/green] Extracted {char_count} characters.")
            else:
                console.print(f"[yellow]Warning:[/yellow] No markdown returned for {url}. Falling back to basic snippet.")
                # We fallback to the basic snippet we got from Tavily search
                if fallback_content:
                    scraped_data.append({
                        "url": url,
                        "title": title,
                        "markdown": fallback_content
                    })
                
        except Exception as e:
            console.print(f"[red]Error scraping {url}:[/red] {e}")
            # Instead of crashing the whole pipeline, fallback gently.
            if fallback_content:
                scraped_data.append({
                    "url": url,
                    "title": title,
                    "markdown": fallback_content
                })
            
    return scraped_data
