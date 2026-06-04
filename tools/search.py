import os
from typing import List, Dict, Any
from firecrawl import FirecrawlApp

def search_firecrawl(query: str, limit: int = 3, api_key: str = None) -> List[Dict[str, Any]]:
    """
    Search the web using Firecrawl and return condensed results.
    """
    key = api_key or os.getenv("FIRECRAWL_API_KEY")
    if not key:
        raise ValueError("FIRECRAWL_API_KEY is not set.")
    
    app = FirecrawlApp(api_key=key)
    
    params = {"limit": limit}
    # Note: Firecrawl v1 and v2 search calls
    try:
        response = app.search(query, params=params)
    except Exception as e:
        # Retry with simpler arguments if it fails
        response = app.search(query)
        
    results = []
    
    if isinstance(response, dict):
        data = response.get("data", []) or response.get("web", [])
        if not data and "success" in response:
            # might be direct key results
            pass
        for item in data:
            results.append({
                "title": item.get("title", "No Title"),
                "url": item.get("url", "No URL"),
                "description": item.get("description", "No description available.")
            })
    elif hasattr(response, "success") and response.success:
        data = response.data if hasattr(response, "data") else []
        for item in data:
            if isinstance(item, dict):
                title = item.get("title")
                url = item.get("url")
                description = item.get("description")
            else:
                title = getattr(item, "title", None)
                url = getattr(item, "url", None)
                description = getattr(item, "description", None)
            
            results.append({
                "title": title or "No Title",
                "url": url or "No URL",
                "description": description or "No description available."
            })
    elif hasattr(response, "model_dump"):
        dump = response.model_dump()
        data = dump.get("data", []) or dump.get("web", []) or []
        for item in data:
            results.append({
                "title": item.get("title", "No Title"),
                "url": item.get("url", "No URL"),
                "description": item.get("description", "No description available.")
            })
    elif isinstance(response, list):
        for item in response:
            if isinstance(item, dict):
                results.append({
                    "title": item.get("title", "No Title"),
                    "url": item.get("url", "No URL"),
                    "description": item.get("description", "")
                })
    
    return results[:limit]
