from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from textwrap import dedent

def run_launch_analyst(company_name: str, search_results: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", dedent("""
            You are a senior GTM strategist.
            Analyze the product launch history and competitive positioning of the target company based on the search results provided.
            
            Produce up to 16 evidence-based insight bullets.
            Format requirements:
            • Start every bullet with exactly one tag: Positioning | Strength | Weakness | Learning
            • Follow the tag with a concise statement (max 30 words) referencing concrete observations: messaging, differentiation, pricing, channel selection, timing, engagement metrics, or customer feedback.
            Be extremely concise. Use only the provided search results.
            IMPORTANT: End with a 'Sources:' section listing the source URLs used.
        """)),
        ("human", "Analyze the company: {company_name}\n\nSearch Results:\n{search_results}")
    ])
    
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    chain = prompt | llm
    res = chain.invoke({"company_name": company_name, "search_results": search_results})
    return res.content
