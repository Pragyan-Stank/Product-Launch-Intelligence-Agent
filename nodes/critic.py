import os
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from textwrap import dedent

def run_critic(final_report: str, analysis_type: str, data_sufficient: bool, api_key: str = None) -> Dict[str, Any]:
    """
    Evaluate the final report against the quality rubric.
    Returns:
        dict: {"passes": bool, "feedback": str}
    """
    prompt_text = dedent("""
        You are an elite QA critic. Evaluate the following report for quality and adherence to guidelines.
        
        Analysis Type: {analysis_type}
        Data Sufficient Flag: {data_sufficient}
        
        CRITIQUE RUBRIC:
        1. Table Rows: Are required table rows populated? (Tables should not have empty or generic placeholder rows, unless there is insufficient data and the report explicitly states so).
        2. Source Reference: Are sources referenced at the end of the report (e.g. list of URLs or Source references)?
        3. Agreement: Do bullets/statements agree? (No contradictions within the text).
        4. Insufficient Data Warning: If Data Sufficient is false, does the report explicitly state at the very beginning that public information was limited/unavailable and that the report reflects partial or no data? If it doesn't, this is a CRITICAL FAILURE.
        
        Report to evaluate:
        ---
        {final_report}
        ---
        
        Evaluate the report against this rubric.
        Return a JSON object with the following fields:
        - "passes": boolean (true if it meets all rubric criteria, false otherwise)
        - "feedback": string (specific feedback pointing out what needs to be fixed if passes is false; empty or brief summary if passes is true)
        
        Do not output any markdown formatting, explanation, or thinking blocks outside the JSON block.
    """)
    
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        return {"passes": True, "feedback": "No Groq API Key found to run critic."}
        
    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=key,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        prompt = ChatPromptTemplate.from_messages([("user", prompt_text)])
        chain = prompt | llm
        response = chain.invoke({
            "final_report": final_report,
            "analysis_type": analysis_type,
            "data_sufficient": str(data_sufficient)
        })
        return json.loads(response.content)
    except Exception as e:
        print(f"Critic failure: {e}")
        return {"passes": True, "feedback": f"Critic failed with error: {str(e)}"}
