from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from textwrap import dedent

def run_sentiment_analyst(company_name: str, search_results: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", dedent("""
            You are a market research expert tracking consumer perception.
            Analyze the market sentiment about the target company's recent launches based on the search results provided.
            
            Summarize market sentiment in <= 10 bullets.
            Cover top positive & negative themes with source mentions (G2, Reddit, Twitter, customer reviews).
            Be extremely concise.
            IMPORTANT: End with a 'Sources:' section listing the source URLs used.
        """)),
        ("human", "Analyze the company: {company_name}\n\nSearch Results:\n{search_results}")
    ])
    
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    chain = prompt | llm
    res = chain.invoke({"company_name": company_name, "search_results": search_results})
    return res.content
