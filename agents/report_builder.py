from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from textwrap import dedent

def run_report_builder(
    bullet_text: str,
    company_name: str,
    analysis_type: str,
    data_sufficient: bool = True,
    critic_feedback: str = None
) -> str:
    # Build warnings/revisions if applicable
    insufficient_warning = ""
    if not data_sufficient:
        insufficient_warning = dedent(f"""
            
            CRITICAL WARNING: The data search results were insufficient. You MUST explicitly and clearly state at the very beginning of the report (e.g. in a clear warning block/callout) that public information for {company_name} was limited/unavailable and that this report reflects partial or no data. Do NOT fabricate data or details to fill in gaps.
        """)
        
    revision_instruction = ""
    if critic_feedback:
        revision_instruction = dedent(f"""
            
            CRITICAL REVISION INSTRUCTION:
            Your previous draft was rejected. You MUST revise the report to address the following feedback from the critic:
            {critic_feedback}
        """)

    if analysis_type == "competitor":
        system_prompt = dedent(f"""
            You are a senior GTM strategist.
            Transform the insight bullets below into a professional launch review for product managers analysing {company_name}.
            
            Produce well-structured **Markdown** with a mix of tables, call-outs and concise bullet points — avoid long paragraphs.
            
            === FORMAT SPECIFICATION ===
            # {company_name} – Launch Review
            
            ## 1. Market & Product Positioning
            • Bullet point summary of how the product is positioned (max 6 bullets).
            
            ## 2. Launch Strengths
            | Strength | Evidence / Rationale |
            |---|---|
            (add 4-6 rows of strengths)
            
            ## 3. Launch Weaknesses
            | Weakness | Evidence / Rationale |
            |---|---|
            (add 4-6 rows of weaknesses)
            
            ## 4. Strategic Takeaways for Competitors
            1. (max 5 numbered recommendations)
            
            Guidelines:
            • Populate the tables with specific points derived from the source bullets.
            • Only include rows that contain meaningful data; omit any blank entries.
            • Keep descriptions concise to avoid excessive token usage.
        """)
        human_prompt = f"=== SOURCE BULLETS ===\n{bullet_text}"
        
    elif analysis_type == "sentiment":
        system_prompt = dedent(f"""
            You are a market sentiment specialist.
            Use the tagged bullets below to create a concise market-sentiment brief for **{company_name}**.
            
            === FORMAT SPECIFICATION ===
            ### Positive Sentiment
            • List each positive point as a separate bullet (max 6).
            
            ### Negative Sentiment
            • List each negative point as a separate bullet (max 6).
            
            ### Overall Summary
            Provide a short paragraph (≤120 words) summarising the overall sentiment balance and key drivers.
            
            Guidelines:
            • Make sure positive and negative points are directly extracted from the source bullets.
            • Stay strictly under the word counts.
        """)
        human_prompt = f"Tagged Bullets:\n{bullet_text}"
        
    elif analysis_type == "metrics":
        system_prompt = dedent(f"""
            You are an executive metric dashboard builder.
            Convert the KPI bullets below into a launch-performance snapshot for **{company_name}** suitable for an executive dashboard.
            
            === FORMAT SPECIFICATION ===
            ## Key Performance Indicators
            | Metric | Value / Detail | Source |
            |---|---|---|
            (include one row per KPI)
            
            ## Qualitative Signals
            • Bullet list of notable qualitative insights (max 5).
            
            ## Summary & Implications
            Brief paragraph (≤120 words) highlighting what the metrics imply about launch success and next steps.
            
            Guidelines:
            • Extract data accurately from the KPI bullets.
            • Do not invent metrics.
        """)
        human_prompt = f"KPI Bullets:\n{bullet_text}"
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")
        
    # Append any dynamic instructions to system_prompt
    system_prompt += insufficient_warning + revision_instruction
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    chain = prompt | llm
    res = chain.invoke({})
    return res.content
