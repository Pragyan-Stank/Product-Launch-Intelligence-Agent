from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from textwrap import dedent

def run_metrics_analyst(company_name: str, search_results: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", dedent("""
            You are a performance analyst tracking launch KPIs.
            Analyze the performance metrics of the target company's recent launches based on the search results provided.
            
            List (max 10 bullets) the most important publicly available KPIs & qualitative signals.
            Include engagement stats, press coverage, adoption metrics, and market traction data if available.
            Focus on factual data from recent press.
            IMPORTANT: End with a 'Sources:' section listing the source URLs used.
        """)),
        ("human", "Analyze the company: {company_name}\n\nSearch Results:\n{search_results}")
    ])
    
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    chain = prompt | llm
    res = chain.invoke({"company_name": company_name, "search_results": search_results})
    return res.content
