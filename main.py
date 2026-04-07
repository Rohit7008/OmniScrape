"""
OmniScrape AI - Main CLI Entry Point
"""
import os
import argparse
import time
import logging
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Configure logging to write to file for debugging
logging.basicConfig(
    filename='omniscrape.log',
    filemode='a',
    format='%(asctime)s [%(levelname)s] - %(message)s',
    level=logging.INFO
)

# Import modules
from src.search import get_latest_news, get_hni_news
from src.scraper import scrape_urls
from src.synthesizer import generate_report
from src.extractors.daily_liquidity import find_new_hnis_today

console = Console()

def normalize_value(val) -> str:
    """Formats dicts and lists into clean human-readable text strings."""
    if isinstance(val, list):
        if not val:
            return "None"
        if all(isinstance(x, dict) for x in val):
            lines = []
            for item in val:
                parts = [f"{k}: {v}" for k, v in item.items() if v]
                lines.append("- " + ", ".join(parts))
            return "\n".join(lines)
        else:
            return "\n".join([f"- {str(x)}" for x in val])
    elif isinstance(val, dict):
        lines = [f"- {k}: {v}" for k, v in val.items() if v]
        return "\n".join(lines)
    else:
        return str(val).strip()

def run_direct_pipeline(target_name: str, company: str, limit: int):
    """Direct Inbound Lead search flow."""
    from src.sheets import check_if_lead_exists, append_direct_lead
    console.print(Panel.fit(f"[bold magenta]OmniScrape AI: DIRECT INBOUND MODE[/bold magenta]\nTarget: [white]{target_name}[/white]\nCompany: [white]{company}[/white]", border_style="yellow"))
    logging.info(f"Starting DIRECT pipeline for: {target_name} | Company: {company}")
    
    if check_if_lead_exists(target_name):
        console.print(f"[bold green]✓ Awesome! Lead '{target_name}' is already enriched in your Google Sheet database![/bold green]")
        console.print("[dim]Skipping API searches to save credits.[/dim]")
        return
        
    try:
        console.print("\n[bold yellow]Phase 1:[/bold yellow] Searching Web (Tavily)")
        # Make the company mandatory in the deal_context search
        deal_ctx = f"Associated with company: {company}"
        urls_to_scrape = get_hni_news(query=target_name, limit=limit, deal_context=deal_ctx)
        
        if not urls_to_scrape:
            console.print("[red]No URLs found. Skipping.[/red]")
            return
            
        for u in urls_to_scrape:
            console.print(f"  - {u.get('url')}")
            
        console.print("\n[bold yellow]Phase 2:[/bold yellow] Deep Extracting Markdown (Firecrawl)")
        scraped_data = scrape_urls(urls_to_scrape)
        
        if not scraped_data:
            console.print("[red]Failed to extract any text. Skipping.[/red]")
            return
            
        console.print("\n[bold yellow]Phase 3:[/bold yellow] Synthesizing Intelligence (Gemini 2.5 Flash)")
        final_markdown = generate_report(scraped_data, target_name, "hni_lead", deal_ctx)
        
        import json
        row_dict = json.loads(final_markdown)
        for k, v in row_dict.items():
            row_dict[k] = normalize_value(v)
            
        safe_name = row_dict.get('Target Name', target_name).replace(" ", "_").lower()
        md_filename = f"output/{safe_name}_direct_report.md"
        
        md_content = f"# Inbound Lead Profile Extract: {row_dict.get('Target Name', target_name)}\n\n"
        for k, v in row_dict.items():
            md_content += f"### {k}\n{v}\n\n"
        
        os.makedirs("output", exist_ok=True)
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        console.print(f"[cyan]Logging new Inbound Lead straight to database...[/cyan]")
        append_direct_lead(target_name, row_dict, company)
        
    except Exception as e:
        console.print(f"[bold red]Pipeline Error for {target_name}:[/bold red] {e}\n")
        logging.exception(f"Pipeline crashed for direct lead {target_name}")

def run_pipeline(target_name: str, entity_type: str, limit: int, is_hni: bool = False, deal_context: str = "", bse_metadata: dict = None):
    """Runs the full intelligence pipeline for a specific target."""
    console.print(Panel.fit(f"[bold magenta]OmniScrape AI Pipeline[/bold magenta]\nTarget: [white]{target_name}[/white]\nType: [white]{entity_type}[/white]", border_style="cyan"))
    logging.info(f"Starting pipeline for target: {target_name} | Type: {entity_type} | HNI Mode: {is_hni}")
    
    try:
        # 1. Search Phase
        console.print("\n[bold yellow]Phase 1:[/bold yellow] Searching Web (Tavily)")
        if is_hni:
            urls_to_scrape = get_hni_news(query=target_name, limit=limit, deal_context=deal_context)
        else:
            urls_to_scrape = get_latest_news(query=target_name, limit=limit)
        
        if not urls_to_scrape:
            console.print("[red]No URLs found. Skipping.[/red]")
            logging.warning(f"No URLs found during Tavily search for {target_name}")
            return
            
        for u in urls_to_scrape:
            console.print(f"  - {u.get('url')}")
            
        # 2. Scrape Phase
        console.print("\n[bold yellow]Phase 2:[/bold yellow] Deep Extracting Markdown (Firecrawl)")
        scraped_data = scrape_urls(urls_to_scrape)
        
        if not scraped_data:
            console.print("[red]Failed to extract any text. Skipping.[/red]")
            logging.error(f"Firecrawl failed to extract text from retrieved URLs for {target_name}")
            return
            
        # 3. Synthesis Phase
        console.print("\n[bold yellow]Phase 3:[/bold yellow] Synthesizing Intelligence (Gemini 2.5 Flash)")
        console.print("[dim]Analyzing scraped data... this may take 10-20 seconds.[/dim]")
        
        start_time = time.time()
        final_markdown = generate_report(scraped_data, target_name, entity_type, deal_context)
        elapsed = time.time() - start_time
        
        console.print(f"[green]Report generated in {elapsed:.1f}s![/green]")
        
        if is_hni:
            import json
            import os
            try:
                console.print("[dim]Parsing Gemini extraction into strict JSON...[/dim]")
                row_dict = json.loads(final_markdown)
                
                for k, v in row_dict.items():
                    row_dict[k] = normalize_value(v)
                
                os.makedirs("output", exist_ok=True)
                safe_name = row_dict.get('Target Name', target_name).replace(" ", "_").lower()
                md_filename = f"output/{safe_name}_report.md"
                
                md_content = f"# Deep Profile Extract: {row_dict.get('Target Name', target_name)}\n\n"
                for k, v in row_dict.items():
                    md_content += f"### {k}\n{v}\n\n"
                
                with open(md_filename, "w", encoding="utf-8") as f:
                    f.write(md_content)
                console.print(f"[green]Saved detailed Markdown report to {md_filename}[/green]")
                # ------------------------------------------------------------------------------
                
                console.print(f"[cyan]Initiating database update for {row_dict.get('Target Name', target_name)}...[/cyan]")
                from src.sheets import update_enriched_row
                update_enriched_row(row_dict.get('Target Name', target_name), row_dict, bse_metadata)
                
            except Exception as e:
                console.print(f"[red]Failed to parse JSON for Google Sheets:[/red] {e}")
                logging.error(f"JSON parsing for {target_name} failed: {e}")
                # Save as a fallback json
                with open(f"output/{target_name.replace(' ', '_').lower()}_fallback.json", "w", encoding="utf-8") as f:
                    f.write(final_markdown)
        else:
            # 4. Output standard Markdown
            os.makedirs("output", exist_ok=True)
            safe_name = target_name.replace(" ", "_").lower()
            filename = f"output/{safe_name}_report.md"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(final_markdown)
                
            console.print(f"\n[bold green]Success![/bold green] Report saved to: [underline]{filename}[/underline]\n")
            
            print("\n--- PREVIEW ---")
            print(final_markdown[:800] + "\n...[TRUNCATED]...")
        
    except Exception as e:
        console.print(f"[bold red]Pipeline Error for {target_name}:[/bold red] {e}\n")
        logging.exception(f"Pipeline crashed for {target_name}")


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="OmniScrape AI: Real-Time Web Intelligence")
    parser.add_argument("--mode", type=str, choices=["standard", "hni_sourcing", "direct"], default="standard", help="Operating mode. 'hni_sourcing' runs Idea 1 automatically. 'direct' is for exact matched leads.")
    parser.add_argument("--phase2_only", action="store_true", help="Skip Phase 1 table generation and only run OmniScrape deep extraction")
    parser.add_argument("--name", type=str, help="Name of the person or company to analyze")
    parser.add_argument("--company", type=str, help="Company Name (Required for Direct Inbound Mode to ensure accurate matching)")
    parser.add_argument("--type", type=str, choices=["person", "company"], default="person", help="Type of entity (Standard Mode)")
    parser.add_argument("--limit", type=int, default=5, help="Max deep URLs to scrape (save Firecrawl credits)")
    parser.add_argument("--source", type=str, choices=["all", "bse", "nse", "insider_screener"], default="all", help="Target specific Phase 1 scraper. 'all' runs all available sources.")
    
    args = parser.parse_args()
    
    if args.mode == "hni_sourcing":
        console.print(Panel.fit("[bold magenta]OmniScrape AI: HNI Sourcing Mode (Idea 1)[/bold magenta]", border_style="green"))
        
        # --- PHASE 1 ---
        if not args.phase2_only:
            from src.extractors.bse_direct import get_bse_bulk_deal_names
            from src.extractors.nse_direct import get_nse_bulk_deal_names
            from src.extractors.insider_screener import get_insider_screener_deals
            
            console.print(f"\n[bold yellow]--- PHASE 1: Multi-Source Base Triage & Database Sync ({args.source}) ---[/bold yellow]")
            
            bse_targets = []
            if args.source in ["all", "bse"]:
                bse_targets = get_bse_bulk_deal_names()
                
            nse_targets = []
            if args.source in ["all", "nse"]:
                nse_targets = get_nse_bulk_deal_names()
                
            insider_targets = []
            if args.source in ["all", "insider_screener"]:
                insider_targets = get_insider_screener_deals()
            
            # Merge Extraction Queues
            all_targets = (bse_targets if isinstance(bse_targets, list) else []) + (nse_targets if isinstance(nse_targets, list) else []) + (insider_targets if isinstance(insider_targets, list) else [])
            
            console.print(f"\n[bold green]✓ Phase 1 Extraction Complete![/bold green]")
            console.print(f"  - Detected [cyan]{len(bse_targets if isinstance(bse_targets, list) else [])}[/cyan] targets from BSE")
            console.print(f"  - Detected [cyan]{len(nse_targets if isinstance(nse_targets, list) else [])}[/cyan] targets from NSE")
            console.print(f"  - Detected [cyan]{len(insider_targets if isinstance(insider_targets, list) else [])}[/cyan] targets from InsiderScreener")
            
            if all_targets:
                from src.sheets import append_base_rows_bulk
                valid_targets = [t for t in all_targets if isinstance(t, dict)]
                append_base_rows_bulk(valid_targets)
            else:
                console.print("[yellow]No new major liquidity events detected today from the BSE or NSE Boards.[/yellow]")
        else:
            console.print("[dim]--- Skipping PHASE 1 (Base Triage) as requested ---[/dim]")
            
        # --- PHASE 2 ---
        console.print("\n[bold yellow]--- PHASE 2: Fetching Pending Queue from Database ---[/bold yellow]")
        from src.sheets import get_targets_from_sheet
        pending_targets = get_targets_from_sheet()
        
        # TEST CONSTRAINT: Only process 2 pending targets per run to save credits
        limited_targets = pending_targets[:2]
        
        if not limited_targets:
            console.print("[bold green]Awesome! No pending targets available. All profiles in your database are already fully enriched (Marked 'Done')![/bold green]")
            return
        
        console.print(f"\n[bold yellow]--- PHASE 2: OmniScrape Deep Profile Extraction (Testing {len(limited_targets)} Targets) ---[/bold yellow]")
        for target_obj in limited_targets:
            if isinstance(target_obj, dict) and "name" in target_obj:
                name = target_obj["name"]
                deal_ctx = target_obj.get("deal_context", "")
                meta = target_obj
            else:
                name = str(target_obj)
                deal_ctx = ""
                meta = None
                
            run_pipeline(target_name=name, entity_type="hni_lead", limit=args.limit, is_hni=True, deal_context=deal_ctx, bse_metadata=meta)
            time.sleep(5)
            
    elif args.mode == "direct":
        if not args.name or not args.company:
            console.print("[red]Error: Both --name and --company are required for Direct Inbound Searches![/red]")
            return
        run_direct_pipeline(target_name=args.name, company=args.company, limit=args.limit)
        
    else:
        # Standard Mode
        if not args.name:
            console.print("[red]Error: --name is required in standard mode.[/red]")
            return
        run_pipeline(target_name=args.name, entity_type=args.type, limit=args.limit, is_hni=False)

if __name__ == "__main__":
    main()
