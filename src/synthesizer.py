"""
Module to interact with Gemini 1.5 Flash
"""
import os
import google.generativeai as genai
from .prompt import get_system_prompt

def init_gemini():
    """Setup Gemini Client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_key":
        raise ValueError("Missing GEMINI_API_KEY in .env")
    genai.configure(api_key=api_key)

def generate_report(scraped_data: list, entity_name: str, entity_type: str = "person", deal_context: str = "") -> str:
    """Takes the raw markdown and outputs an intelligence report."""
    init_gemini()
    
    # 1. Combine Markdown into a single massive context string
    # We will also inject the URLs so Gemini knows how to cite them.
    context_chunks = []
    for idx, item in enumerate(scraped_data):
        url = item.get("url", "Unknown URL")
        title = item.get("title", "Unknown Title")
        markdown = item.get("markdown", "")
        
        chunk = f"--- START OF SOURCE {idx + 1} ---\n"
        chunk += f"URL: {url}\n"
        chunk += f"Title: {title}\n"
        chunk += f"Content:\n{markdown[:100000]}\n" # Truncate heavily to fit within context/token limits
        chunk += f"--- END OF SOURCE {idx + 1} ---\n"
        context_chunks.append(chunk)
        
    compiled_context = "\n".join(context_chunks)
    
    # Cap total character size to prevent overwhelming the flash model payload size 
    if len(compiled_context) > 600000:
        compiled_context = compiled_context[:600000] + "\n...[CONTEXT TRUNCATED]"
        
    if entity_type == "hni_lead":
        from .prompt import get_hni_system_prompt
        system_instruction = get_hni_system_prompt(deal_context)
    else:
        system_instruction = get_system_prompt(entity_type)
    
    prompt = f"""
TARGET ENTITY: {entity_name}
ENTITY TYPE: {entity_type}

You must process the following raw scraped data and output the final intelligence report.

{compiled_context}
"""
    
    generation_config = {
        "temperature": 0.2, 
        "top_p": 0.95,
        "max_output_tokens": 8192,
    }
    
    if entity_type == "hni_lead":
        generation_config["response_mime_type"] = "application/json"
        
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config,
        system_instruction=system_instruction
    )
    
    # Retry loop for 429 quota limits
    response = None
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            break
        except Exception as e:
            if "429" in str(e):
                from rich.console import Console
                Console().print(f"[yellow]Synthesizer hit Quota limit (429). Waiting 35s... (Attempt {attempt+1}/3)[/yellow]")
                import time
                time.sleep(35)
            else:
                raise e
    
    if not response:
        return "{}"
    
    return response.text
