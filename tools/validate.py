import os
import re
import json
from typing import List, Dict, Any, Tuple
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from textwrap import dedent

BLOCK_SIGNATURES = [
    "access denied",
    "pardon our interruption",
    "cloudflare",
    "enable javascript",
    "checking your browser",
    "403 forbidden",
    "404 not found",
    "robots.txt",
    "security check",
    "captcha",
    "just a moment",
    "please turn on javascript",
    "access to this page has been denied",
    "ip address",
    "ddos protection"
]

def clean_and_filter_programmatic(results: List[Dict[str, Any]], company_name: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Perform fast programmatic checks on the search results.
    Returns:
        - passed: list of results that passed programmatic checks
        - failed: list of results that failed
        - log_markdown: markdown representation of the checks
    """
    passed = []
    failed = []
    log_lines = []
    
    comp_lower = company_name.lower()
    
    for idx, r in enumerate(results):
        title = r.get("title", "").strip()
        url = r.get("url", "").strip()
        desc = r.get("description", "").strip()
        
        desc_lower = desc.lower()
        title_lower = title.lower()
        
        # Check 1: Scraper Block/Error Check
        block_found = False
        for sig in BLOCK_SIGNATURES:
            if sig in desc_lower or sig in title_lower:
                block_found = True
                r_failed = r.copy()
                r_failed["reason"] = f"Crawler block detected ('{sig}')"
                failed.append(r_failed)
                log_lines.append(f"- **{title or url}**: ⚠️ Programmatically Filtered - Scraper/Access Block.")
                break
        
        if block_found:
            continue
            
        # Check 2: Relevance check (company name mention)
        # Let's check if the company name appears as a substring in title, description, or URL.
        if comp_lower not in desc_lower and comp_lower not in title_lower and comp_lower not in url.lower():
            r_failed = r.copy()
            r_failed["reason"] = f"Company name '{company_name}' not mentioned in metadata"
            failed.append(r_failed)
            log_lines.append(f"- **{title or url}**: ⚠️ Programmatically Filtered - Unrelated to {company_name}.")
            continue
            
        passed.append(r)
        
    return passed, failed, "\n".join(log_lines)

def validate_results_with_llm(results: List[Dict[str, Any]], company_name: str, api_key: str = None) -> Tuple[List[Dict[str, Any]], str]:
    """
    Validate search results using LLM for relevance and freshness.
    Returns:
        - validated_results: list of results that are approved by LLM
        - validation_log: markdown log of validation decisions
    """
    if not results:
        return [], ""
        
    formatted_results = []
    for idx, r in enumerate(results):
        formatted_results.append(
            f"--- RESULT {idx} ---\n"
            f"Title: {r.get('title')}\n"
            f"URL: {r.get('url')}\n"
            f"Description: {r.get('description')}\n"
        )
    results_str = "\n".join(formatted_results)
    
    prompt_text = dedent("""
        You are a search validator. Evaluate the following search results for the target company '{company_name}'.
        We are in the year **2026**.
        
        For each search result, check if it is:
        1. **Relevant**: Directly about the company '{company_name}' and their product launches, marketing, adoption, or sentiment.
        2. **Legitimate**: Not a crawler block page, login wall, broken link, or standard cookie page.
        3. **Fresh/Recent**: Refers to recent product launches (ideally from 2024 to 2026). If the content refers strictly to very old historical events (like iPhone 4, or events prior to 2023) and contains no recent context, mark it as NOT fresh.
        
        Evaluate the following results:
        {results_str}
        
        You must return a JSON object with a single key 'results' mapping to an array of objects.
        Do NOT return any explanation, introduction, or Markdown formatting outside the JSON block.
        
        CRITICAL: The 'reason' field for each result MUST be a non-empty explanation (at least 5 words) justifying why the result is relevant, recent, and legitimate (or why it was rejected).
        
        Format example:
        {{
          "results": [
            {{
              "index": 0,
              "is_legit": true,
              "is_recent": true,
              "is_relevant": true,
              "reason": "Mentions Tesla's late 2025 Model Y updates and 2026 plans."
            }},
            ...
          ]
        }}
    """)
    
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        # Fallback if no key is found at this stage
        evals = [{"index": idx, "is_legit": True, "is_recent": True, "is_relevant": True, "reason": "No Groq API Key found for validation"} for idx in range(len(results))]
    else:
        try:
            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                temperature=0,
                api_key=key,
                model_kwargs={"response_format": {"type": "json_object"}}
            )
            prompt = ChatPromptTemplate.from_messages([("user", prompt_text)])
            chain = prompt | llm
            response = chain.invoke({"company_name": company_name, "results_str": results_str})
            try:
                os.makedirs("outputs", exist_ok=True)
                with open("outputs/validation_raw.json", "w", encoding="utf-8") as f_raw:
                    f_raw.write(response.content)
            except Exception:
                pass
            data = json.loads(response.content)
            evals = data.get("results", [])
        except Exception as e:
            evals = []
            for idx in range(len(results)):
                evals.append({
                    "index": idx,
                    "is_legit": True,
                    "is_recent": True,
                    "is_relevant": True,
                    "reason": f"Validation fallback due to error: {str(e)}"
                })
            
    validated = []
    log_lines = []
    
    for ev in evals:
        idx = ev.get("index")
        if idx is None or idx < 0 or idx >= len(results):
            continue
            
        r = results[idx]
        is_legit = ev.get("is_legit", True)
        is_recent = ev.get("is_recent", True)
        is_relevant = ev.get("is_relevant", True)
        reason = ev.get("reason", "")
        
        title = r.get("title", "No Title")
        
        if is_legit and is_recent and is_relevant:
            validated.append(r)
            log_lines.append(f"- **{title}**: ✅ Verified - {reason}")
        else:
            reasons = []
            if not is_relevant:
                reasons.append("Irrelevant")
            if not is_recent:
                reasons.append("Outdated")
            if not is_legit:
                reasons.append("Non-legitimate/Scraper issue")
                
            reasons_str = " & ".join(reasons)
            log_lines.append(f"- **{title}**: ❌ Filtered ({reasons_str}) - {reason}")
            
    return validated, "\n".join(log_lines)

def validate_search_results(results: List[Dict[str, Any]], company_name: str, api_key: str = None) -> Tuple[List[Dict[str, Any]], str]:
    """
    Full validation pipeline. Runs programmatic filters first, then passes survivors to LLM.
    Returns:
        - final_results: list of validated/fresh search results
        - log_markdown: user-friendly validation report
    """
    if not results:
        return [], "No search results fetched."
        
    passed_prog, failed_prog, prog_log = clean_and_filter_programmatic(results, company_name)
    
    validated, llm_log = validate_results_with_llm(passed_prog, company_name, api_key)
    
    # Fallback mechanism: if LLM filtered out everything, but we have programmatic survivors, use those.
    final_results = validated
    fallback_note = ""
    if not validated and passed_prog:
        final_results = passed_prog
        fallback_note = "\n\n*Note: All results were filtered by strict LLM rules; fell back to programmatic clean results.*"
    elif not final_results and results:
        # Extreme fallback: use original results if absolutely everything failed validation
        final_results = results
        fallback_note = "\n\n*Warning: No results passed validation checks; fell back to raw search results.*"
        
    all_logs = []
    if prog_log:
        all_logs.append(prog_log)
    if llm_log:
        all_logs.append(llm_log)
        
    log_markdown = "\n".join(all_logs) if all_logs else "No validation logs."
    if fallback_note:
        log_markdown += fallback_note
        
    return final_results, log_markdown
