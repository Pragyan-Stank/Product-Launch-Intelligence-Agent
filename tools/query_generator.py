import os
import json
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from textwrap import dedent

def generate_queries(
    company_name: str,
    analysis_type: str,
    previous_queries: Optional[List[str]] = None,
    validation_summary: Optional[str] = None,
    api_key: str = None
) -> List[str]:
    """
    Generate 2-3 distinct search queries for a company based on analysis type.
    If previous queries and validation summary are provided, generates refined queries.
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        # Fallback if no API key is available (mostly for testing / robustness)
        if analysis_type == "competitor":
            return [
                f"{company_name} product launch positioning strengths weaknesses",
                f"{company_name} competitive landscape GTM strategy"
            ]
        elif analysis_type == "sentiment":
            return [
                f"{company_name} product reviews customer feedback",
                f"{company_name} customer complaints forum discussions"
            ]
        else:
            return [
                f"{company_name} revenue adoption metrics",
                f"{company_name} market share growth KPIs"
            ]

    # Structure the prompt
    if previous_queries and validation_summary:
        # Refinement prompt
        prompt_text = dedent("""
            You are a search query refinement specialist. We need to find web content about the company '{company_name}' for a '{analysis_type}' analysis.
            We are in the year **2026**.
            
            Our previous search queries failed or returned insufficient/unusable results.
            
            PREVIOUS QUERIES:
            {previous_queries}
            
            VALIDATION FAILURE SUMMARY:
            {validation_summary}
            
            Generate a new, DIFFERENT set of 2-3 distinct search query strings to find better information.
            Guidelines:
            - Try to broaden the search (e.g. drop specific date constraints, drop overly specific keywords).
            - Try generic terms like "{company_name} overview", "{company_name} funding", or "{company_name} business model".
            - Address wrong-company disambiguation if mentioned in the failure summary.
            - Do NOT use site: operators, punctuation (quotes, OR, AND), or hardcode platform names. Use natural language query phrasing.
            - Focus on finding diverse source types (official, community discussion, news).
            
            You must return a JSON object with a single key 'queries' mapping to an array of 2-3 string queries.
            Do not include any explanation or markdown code blocks outside of the JSON block.
            
            Format example:
            {{
              "queries": [
                "query one",
                "query two"
              ]
            }}
        """)
        human_input = f"Refining search for {company_name} ({analysis_type})"
    else:
        # Initial queries prompt
        prompt_text = dedent("""
            You are a search query generation specialist. We need to find web content about the company '{company_name}' to perform a '{analysis_type}' analysis.
            We are in the year **2026**.
            
            Generate a set of 2-3 distinct search query strings to find high-quality, relevant results.
            Guidelines:
            - Focus on diverse source types: official press/positioning, community/review discussions, recent news/metrics.
            - Do NOT use site: operators or hardcode specific platform names (like LinkedIn) to avoid scraper block walls.
            - Use natural language phrasing. Example: "{company_name} reviews Reddit" or "{company_name} customer complaints".
            - Keep queries distinct to cover different aspects of the analysis type:
              - competitor: positioning, strengths, weaknesses, product features.
              - sentiment: user opinions, customer feedback, reviews, market perception.
              - metrics: adoption rates, user statistics, revenue, KPIs, funding.
            
            You must return a JSON object with a single key 'queries' mapping to an array of 2-3 string queries.
            Do not include any explanation or markdown code blocks outside of the JSON block.
            
            Format example:
            {{
              "queries": [
                "query one",
                "query two",
                "query three"
              ]
            }}
        """)
        human_input = f"Generate search queries for {company_name} ({analysis_type})"
        
    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=key,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_text),
            ("human", human_input)
        ])
        chain = prompt | llm
        
        # Build variables for formatting
        vars = {
            "company_name": company_name,
            "analysis_type": analysis_type
        }
        if previous_queries and validation_summary:
            vars["previous_queries"] = str(previous_queries)
            vars["validation_summary"] = validation_summary
            
        res = chain.invoke(vars)
        data = json.loads(res.content)
        queries = data.get("queries", [])
        if not queries:
            raise ValueError("No queries returned in JSON response")
        return queries
    except Exception as e:
        # Fallback to basic list if anything fails
        print(f"Error generating queries: {e}")
        return [f"{company_name} {analysis_type}"]
