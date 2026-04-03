"""
Module to interact with Google Sheets.
"""
import os
import gspread
from google.oauth2.service_account import Credentials
from rich.console import Console
from datetime import datetime

console = Console()

def init_gspread():
    """Initializes the gspread client."""
    client_email = os.getenv("GOOGLE_CLIENT_EMAIL")
    private_key = os.getenv("GOOGLE_PRIVATE_KEY")
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    
    if not all([client_email, private_key, sheet_id]):
        console.print("[yellow]Warning: Google Sheets credentials missing in .env. Skipping export.[/yellow]")
        return None, None
        
    private_key = private_key.replace("\\n", "\n")
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    credentials = Credentials.from_service_account_info(
        {
            "client_email": client_email,
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
            "project_id": "omniscrape-ai"
        },
        scopes=scopes
    )
    
    try:
        client = gspread.authorize(credentials)
        return client, sheet_id
    except Exception as e:
        console.print(f"[red]Failed to authorize Google Sheets API:[/red] {e}")
        return None, None

def get_or_create_headers(sheet):
    """Ensures the Google Sheet has the correct headers on row 1."""
    headers = [
        "Source",
        "Target Name",
        "Deal Date",
        "Deal Type",
        "Quantity",
        "Price",
        "Liquidity Event Description",
        "Estimated Quantum (₹)",
        "Active Companies / Directorships",
        "Financial Health (Revenue/Capital)",
        "Warm Intro Paths (Lawyers/CAs)",
        "Profile Notes / Philanthropy",
        "Source Verification Links",
        "Date Added",
        "Status",
        "Phase 1 Timestamp",
        "Phase 2 Timestamp"
    ]
    
    try:
        # Securely check A1 to see if headers exist, bypassing "empty list" logic which fails on blank string grids
        first_row = sheet.get("A1:Q1")
        if not first_row or not first_row[0] or first_row[0][0] != "Source":
            console.print("[cyan]Headers missing or incorrect. Enforcing Custom Headers at Row 1...[/cyan]")
            sheet.update(range_name="A1:Q1", values=[headers])
            
    except Exception as e:
        console.print(f"[red]Could not verify or set Header Row:[/red] {e}")
        
    return headers

def append_base_rows_bulk(targets: list[dict]):
    """PHASE 1: Appends ALL base targets in a single API call to save quotas and prevent API overlapping."""
    client, sheet_id = init_gspread()
    if not client:
        return
        
    try:
        sheet = client.open_by_key(sheet_id).sheet1
        headers = get_or_create_headers(sheet)
        
        rows_to_insert = []
        
        try:
            # Memory cache existing records to prevent duplicates
            existing_records = sheet.get_all_records()
        except:
            existing_records = []
            
        existing_signatures = set()
        for r in existing_records:
            name_val = str(r.get("Target Name", "")).strip().lower()
            date_val = str(r.get("Deal Date", "")).strip().lower()
            if name_val:
                existing_signatures.add((name_val, date_val))
                
        # Filter incoming targets
        for target_dict in targets:
            t_name = str(target_dict.get("name", "")).strip().lower()
            t_date = str(target_dict.get("deal_date", "")).strip().lower()
            
            # Skip if we already scraped this exact person on this exact date
            if (t_name, t_date) in existing_signatures:
                continue
                
            row_list = [""] * len(headers)
            row_list[0] = str(target_dict.get("source", "BSE")) # Default to BSE if missing for backwards compatibility
            row_list[1] = str(target_dict.get("name", ""))
            row_list[2] = str(target_dict.get("deal_date", ""))
            row_list[3] = str(target_dict.get("deal_type", ""))
            row_list[4] = str(target_dict.get("quantity", ""))
            row_list[5] = str(target_dict.get("price", ""))
            row_list[6] = str(target_dict.get("deal_context", "")) # Save exact context for Phase 2!
            row_list[8] = str(target_dict.get("network_context", "")) # Col I: Active Companies / Directorships (Natively pushed during Phase 1 for InsiderScreener)
            row_list[13] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Date Added
            row_list[14] = "Pending" # Status
            row_list[15] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Phase 1 Timestamp
            row_list[16] = "" # Phase 2 Timestamp
            rows_to_insert.append(row_list)
            
        if rows_to_insert:
            sheet.append_rows(rows_to_insert)
            console.print(f"[bold green]✓ PHASE 1 Database Save: {len(rows_to_insert)} *new* targets stored simultaneously via Base Scrape![/bold green]")
        else:
            console.print("[dim]✓ PHASE 1 Database Save: All scraped targets already exist in the database. No new rows added.[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error saving Base Targets to Google Sheets:[/red] {e}")


def update_enriched_row(target_name: str, enriched_dict: dict, bse_metadata: dict = None):
    """PHASE 2: Searches for the exact Target Name row generated in Phase 1, and updates columns F-P with deep intelligence."""
    client, sheet_id = init_gspread()
    if not client:
        return
        
    try:
        sheet = client.open_by_key(sheet_id).sheet1
        
        try:
            # Shifted to Column 2 because Source is now Col A
            cell = sheet.find(target_name, in_column=2)
            row_idx = cell.row
        except gspread.exceptions.CellNotFound:
            console.print(f"[red]Could not find '{target_name}' in Google Sheets to update during Phase 2![/red]")
            return
            
        update_list = [
            str(enriched_dict.get("Liquidity Event Description", "")),
            str(enriched_dict.get("Estimated Quantum (₹)", "")),
            str(enriched_dict.get("Active Companies / Directorships", "")),
            str(enriched_dict.get("Financial Health (Revenue/Capital)", "")),
            str(enriched_dict.get("Warm Intro Paths (Lawyers/CAs)", "")),
            str(enriched_dict.get("Profile Notes / Philanthropy", "")),
            str(enriched_dict.get("Source Verification Links", "")),
            bse_metadata.get("date_added", "") if bse_metadata else "", # Col N
            "Done", # Col O (Status)
            bse_metadata.get("phase_1_timestamp", "") if bse_metadata else "", # Col P
            datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Col Q (Phase 2 Timestamp)
        ]
        
        # Update cols G (Liquidity) through Q (Phase 2 Timestamp)
        sheet.update(range_name=f"G{row_idx}:Q{row_idx}", values=[update_list])
        console.print(f"[bold green]✓ PHASE 2 Database Update: {target_name}'s Deep Profile Intelligence merged (Status Set to Done)![/bold green]")
        
    except Exception as e:
        console.print(f"[red]Error updating Enriched Data to Google Sheets:[/red] {e}")

def get_targets_from_sheet() -> list[dict]:
    """Reads Target Names and BSE context directly from Google Sheets to completely skip Phase 1 API quotas. Skips targets already marked 'Done'."""
    client, sheet_id = init_gspread()
    if not client:
        return []
        
    try:
        from rich.console import Console
        console = Console()
        sheet = client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_records()
        
        targets = []
        for r in records:
            status = str(r.get("Status", "")).strip().lower()
            if status == "done":
                continue
                
            name = str(r.get("Target Name", "")).strip()
            if name:
                # Use stored transaction context to help AI differentiate entities
                deal_ctx = str(r.get("Liquidity Event Description", ""))
                if not deal_ctx:
                    deal_ctx = f"Shares of {r.get('Target Name', '')}"
                
                targets.append({
                    "name": name, 
                    "deal_context": deal_ctx,
                    "date_added": str(r.get("Date Added", "")),
                    "phase_1_timestamp": str(r.get("Phase 1 Timestamp", ""))
                })
                
        return targets
        
    except Exception as e:
        from rich.console import Console
        Console().print(f"[red]Error reading targets from Google Sheets:[/red] {e}")
        return []
