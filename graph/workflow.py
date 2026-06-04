from langgraph.graph import StateGraph, END
from graph.state import AgentState
from tools.search import search_firecrawl
from tools.validate import validate_search_results
from agents.launch_analyst import run_launch_analyst
from agents.sentiment_analyst import run_sentiment_analyst
from agents.metrics_analyst import run_metrics_analyst
from agents.report_builder import run_report_builder

# Define node functions
def launch_analyst_node(state: AgentState) -> dict:
    company = state["company_name"]
    # 1. Search Firecrawl with temporal bias
    search_query = f"{company} product launch 2025 2026 positioning strengths weaknesses"
    results = search_firecrawl(search_query, limit=3)
    
    # 2. Validate search results
    validated, val_log = validate_search_results(results, company)
    
    # 3. Format validated results
    formatted = ""
    for r in validated:
        formatted += f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['description']}\n\n"
        
    # 4. Call launch analyst agent
    bullets = run_launch_analyst(company, formatted)
    return {"raw_bullets": bullets, "validation_status": val_log}

def sentiment_analyst_node(state: AgentState) -> dict:
    company = state["company_name"]
    # 1. Search Firecrawl with temporal bias
    search_query = f"{company} product launch 2025 2026 market sentiment customer feedback reviews"
    results = search_firecrawl(search_query, limit=3)
    
    # 2. Validate search results
    validated, val_log = validate_search_results(results, company)
    
    # 3. Format validated results
    formatted = ""
    for r in validated:
        formatted += f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['description']}\n\n"
        
    # 4. Call sentiment analyst agent
    bullets = run_sentiment_analyst(company, formatted)
    return {"raw_bullets": bullets, "validation_status": val_log}

def metrics_analyst_node(state: AgentState) -> dict:
    company = state["company_name"]
    # 1. Search Firecrawl with temporal bias
    search_query = f"{company} product launch 2025 2026 KPIs revenue adoption metrics"
    results = search_firecrawl(search_query, limit=3)
    
    # 2. Validate search results
    validated, val_log = validate_search_results(results, company)
    
    # 3. Format validated results
    formatted = ""
    for r in validated:
        formatted += f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['description']}\n\n"
        
    # 4. Call metrics analyst agent
    bullets = run_metrics_analyst(company, formatted)
    return {"raw_bullets": bullets, "validation_status": val_log}

def report_builder_node(state: AgentState) -> dict:
    bullets = state.get("raw_bullets") or ""
    company = state["company_name"]
    analysis_type = state["analysis_type"]
    
    report = run_report_builder(bullets, company, analysis_type)
    return {"final_report": report}

# Routing function
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

# Build graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("launch_analyst", launch_analyst_node)
workflow.add_node("sentiment_analyst", sentiment_analyst_node)
workflow.add_node("metrics_analyst", metrics_analyst_node)
workflow.add_node("report_builder", report_builder_node)

# Add routing from START
workflow.set_conditional_entry_point(
    router,
    {
        "launch_analyst": "launch_analyst",
        "sentiment_analyst": "sentiment_analyst",
        "metrics_analyst": "metrics_analyst"
    }
)

# Connect analysts to report builder
workflow.add_edge("launch_analyst", "report_builder")
workflow.add_edge("sentiment_analyst", "report_builder")
workflow.add_edge("metrics_analyst", "report_builder")

# Connect report builder to END
workflow.add_edge("report_builder", END)

# Compile graph
app = workflow.compile()
