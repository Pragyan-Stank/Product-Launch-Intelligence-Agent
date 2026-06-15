from langgraph.graph import StateGraph, END
from graph.state import AgentState
from tools.search import search_firecrawl
from tools.validate import validate_search_results
from tools.query_generator import generate_queries
from nodes.launch_analyst import run_launch_analyst
from nodes.sentiment_analyst import run_sentiment_analyst
from nodes.metrics_analyst import run_metrics_analyst
from nodes.report_builder import run_report_builder
from nodes.critic import run_critic
from nodes.entity_validator import run_entity_validator
import streamlit as st
from datetime import date
from typing import Optional, List

# ---- Streamlit Search Cache Helpers ----
def get_cached_search_results(company_name: str, query: str) -> Optional[list]:
    """
    Check if a query has already been run today for the specified company.
    Safe to execute outside Streamlit environments (returns None).
    """
    try:
        # Only query cache if we are executing within a Streamlit context
        if hasattr(st, "runtime") and st.runtime.exists():
            cache_key = f"{company_name}_{date.today()}"
            if "search_cache" not in st.session_state:
                st.session_state["search_cache"] = {}
            company_cache = st.session_state["search_cache"].get(cache_key, {})
            return company_cache.get(query)
    except Exception:
        pass
    return None

def set_cached_search_results(company_name: str, query: str, results: list):
    """
    Store the query search results in the Streamlit session state cache.
    Safe to execute outside Streamlit environments (noop).
    """
    try:
        if hasattr(st, "runtime") and st.runtime.exists():
            cache_key = f"{company_name}_{date.today()}"
            if "search_cache" not in st.session_state:
                st.session_state["search_cache"] = {}
            if cache_key not in st.session_state["search_cache"]:
                st.session_state["search_cache"][cache_key] = {}
            st.session_state["search_cache"][cache_key][query] = results
    except Exception:
        pass

# ---- Common Node Runner helper for Analyst nodes ----
def run_analyst_node(state: AgentState, analysis_type: str, analyst_runner_fn: callable) -> dict:
    company = state.get("company_name")
    retry_count = state.get("retry_count", 0)
    validation_status_accum = state.get("validation_status") or ""
    
    # 1. Determine queries: if retry_count > 0, we already have refined queries generated
    if retry_count > 0 and state.get("search_queries"):
        queries = state["search_queries"]
    else:
        # First attempt: generate initial queries using llama-3.1-8b-instant
        queries = generate_queries(company, analysis_type)
        retry_count = 0  # Initialize explicitly
        
    # 2. Search Firecrawl with cache check
    all_results = []
    seen_urls = set()
    for q in queries:
        cached_res = get_cached_search_results(company, q)
        if cached_res is not None:
            # Cache hit - reuse scraped results to avoid extra API hits
            results = cached_res
        else:
            # Cache miss - call Firecrawl
            results = search_firecrawl(q, limit=3)
            set_cached_search_results(company, q, results)
            
        for r in results:
            url = r.get("url", "").strip().lower()
            if url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)
                
    # 3. Validate results (runs programmatic + LLM judge using llama-3.1-8b-instant)
    validated, val_log = validate_search_results(all_results, company)
    
    # Accumulate validation logs for debugging / demoing retry attempts
    attempt_header = f"### Attempt {retry_count + 1} (Queries: {', '.join(queries)})\n"
    new_val_log = attempt_header + val_log
    if validation_status_accum:
        updated_val_log = validation_status_accum + "\n\n" + new_val_log
    else:
        updated_val_log = new_val_log
        
    # 4. Check data sufficiency condition:
    # Insufficient if we have < 2 results, OR most were filtered (detected via fallback note or few verified ones)
    verified_count = val_log.count("✅ Verified")
    is_insufficient = len(validated) < 2 or verified_count < 2 or "fell back to" in val_log
    
    # 5. Check if we should perform a retry (Hard cap: max 2 retries, i.e., retry_count < 2)
    if is_insufficient and retry_count < 2:
        # Refine queries using previous queries + failure details
        refined_queries = generate_queries(
            company_name=company,
            analysis_type=analysis_type,
            previous_queries=queries,
            validation_summary=val_log
        )
        return {
            "search_queries": refined_queries,
            "retry_count": retry_count + 1,
            "validation_status": updated_val_log,
            "validation_summary": val_log,
            "needs_retry": True
        }
    else:
        # Retries exhausted or data is sufficient. Set data_sufficient flag.
        data_sufficient = not is_insufficient
        
        # Format validated results for the analyst
        formatted = ""
        for r in validated:
            formatted += f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['description']}\n\n"
            
        # Run standard 120B Analyst LLM call
        bullets = analyst_runner_fn(company, formatted)
        
        return {
            "raw_bullets": bullets,
            "validation_status": updated_val_log,
            "data_sufficient": data_sufficient,
            "needs_retry": False,
            "search_queries": queries  # Keep the queries used for UI reporting
        }

# ---- Node Functions ----
def entity_validator_node(state: AgentState) -> dict:
    """
    Validates input entity to ensure it represents a company/brand.
    Handles ambiguous entities by resolving to the company name,
    and flags invalid entities for aborting the pipeline.
    """
    company = state["company_name"]
    result = run_entity_validator(company)
    
    is_valid = result.get("is_valid", True)
    entity_type = result.get("entity_type", "company")
    reason = result.get("reason", "")
    suggested_correction = result.get("suggested_correction")
    
    if entity_type == "ambiguous" and suggested_correction:
        # Accept the correction, overwrite company_name, and report resolved_company_name
        return {
            "entity_valid": True,
            "entity_type": entity_type,
            "company_name": suggested_correction,
            "resolved_company_name": suggested_correction
        }
    elif not is_valid:
        return {
            "entity_valid": False,
            "entity_type": entity_type,
            "abort_reason": reason
        }
    else:
        return {
            "entity_valid": True,
            "entity_type": entity_type
        }

def launch_analyst_node(state: AgentState) -> dict:
    return run_analyst_node(state, "competitor", run_launch_analyst)

def sentiment_analyst_node(state: AgentState) -> dict:
    return run_analyst_node(state, "sentiment", run_sentiment_analyst)

def metrics_analyst_node(state: AgentState) -> dict:
    return run_analyst_node(state, "metrics", run_metrics_analyst)

def report_builder_node(state: AgentState) -> dict:
    bullets = state.get("raw_bullets") or ""
    company = state["company_name"]
    analysis_type = state["analysis_type"]
    data_sufficient = state.get("data_sufficient", True)
    critic_feedback = state.get("critic_feedback")
    
    report = run_report_builder(
        bullets,
        company,
        analysis_type,
        data_sufficient=data_sufficient,
        critic_feedback=critic_feedback
    )
    return {"final_report": report}

def critic_node(state: AgentState) -> dict:
    """
    Evaluates final_report quality against the rubric using llama-3.1-8b-instant.
    """
    final_report = state.get("final_report") or ""
    analysis_type = state["analysis_type"]
    data_sufficient = state.get("data_sufficient", True)
    revision_count = state.get("revision_count", 0)
    
    # Run critique review
    critique = run_critic(final_report, analysis_type, data_sufficient)
    passes = critique.get("passes", True)
    feedback = critique.get("feedback", "")
    
    # If QA checks fail, and we haven't reached the revision cap, request revision
    # Hard cap: max 1 revision (revision_count < 1)
    if not passes and revision_count < 1:
        return {
            "critic_feedback": feedback,
            "revision_count": revision_count + 1,
            "critic_passes": False
        }
    else:
        return {
            "critic_passes": True,
            "critic_feedback": feedback if not passes else None
        }

# ---- Routing Functions ----
def router(state: AgentState) -> str:
    analysis_type = state["analysis_type"]
    if analysis_type == "competitor":
        return "launch_analyst"
    elif analysis_type == "sentiment":
        return "sentiment_analyst"
    elif analysis_type == "metrics":
        return "metrics_analyst"
    else:
        return "launch_analyst"

# Analyst nodes check if they need to loop back for retry
def launch_analyst_router(state: AgentState) -> str:
    if state.get("needs_retry"):
        return "launch_analyst"
    return "report_builder"

def sentiment_analyst_router(state: AgentState) -> str:
    if state.get("needs_retry"):
        return "sentiment_analyst"
    return "report_builder"

def metrics_analyst_router(state: AgentState) -> str:
    if state.get("needs_retry"):
        return "metrics_analyst"
    return "report_builder"

# Critic node checks if it needs to loop back to report builder
def critic_router(state: AgentState) -> str:
    if not state.get("critic_passes", True) and state.get("revision_count", 0) <= 1:
        return "report_builder"
    return "end"

# Entity validator routing function
def entity_validation_router(state: AgentState) -> str:
    if state.get("entity_valid"):
        # Route to original router logic to determine analyst node
        return router(state)
    return "end"

# ---- Build Graph ----
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("entity_validator", entity_validator_node)
workflow.add_node("launch_analyst", launch_analyst_node)
workflow.add_node("sentiment_analyst", sentiment_analyst_node)
workflow.add_node("metrics_analyst", metrics_analyst_node)
workflow.add_node("report_builder", report_builder_node)
workflow.add_node("critic", critic_node)

# Set entry point to entity validator
workflow.set_entry_point("entity_validator")

# Connect entity validator conditionally
workflow.add_conditional_edges(
    "entity_validator",
    entity_validation_router,
    {
        "launch_analyst": "launch_analyst",
        "sentiment_analyst": "sentiment_analyst",
        "metrics_analyst": "metrics_analyst",
        "end": END
    }
)

# Connect analysts conditionally (to support search query retry loops)
workflow.add_conditional_edges(
    "launch_analyst",
    launch_analyst_router,
    {
        "launch_analyst": "launch_analyst",
        "report_builder": "report_builder"
    }
)
workflow.add_conditional_edges(
    "sentiment_analyst",
    sentiment_analyst_router,
    {
        "sentiment_analyst": "sentiment_analyst",
        "report_builder": "report_builder"
    }
)
workflow.add_conditional_edges(
    "metrics_analyst",
    metrics_analyst_router,
    {
        "metrics_analyst": "metrics_analyst",
        "report_builder": "report_builder"
    }
)

# Connect report builder to critic node
workflow.add_edge("report_builder", "critic")

# Connect critic node conditionally (to support report revision loops)
workflow.add_conditional_edges(
    "critic",
    critic_router,
    {
        "report_builder": "report_builder",
        "end": END
    }
)

# Compile graph
app = workflow.compile()


