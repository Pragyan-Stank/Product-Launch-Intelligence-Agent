import os
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from textwrap import dedent

def run_entity_validator(company_name: str, api_key: str = None) -> Dict[str, Any]:
    """
    Validate whether the input company_name represents a valid company, brand, product, or enterprise.
    Identifies and corrects ambiguous inputs (person name + company name) and rejects pure individuals.
    
    Returns a dict:
        {
            "is_valid": bool,
            "entity_type": "company" | "person" | "government" | "ambiguous" | "other",
            "reason": str,
            "suggested_correction": str or None
        }
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    # Fallback to true (fail open) if no API key is set
    if not key:
        return {
            "is_valid": True,
            "entity_type": "company",
            "reason": "Bypassed validation due to missing API key.",
            "suggested_correction": None
        }
        
    prompt_text = dedent("""
        You are an elite input validator. Your job is to classify the input string '{input_name}' to ensure it represents a company, startup, product brand, enterprise, SaaS tool, platform, or app.
        
        CRITICAL CLASSIFICATION RULES:
        1. VALID ('company'):
           - Must be a company, brand, startup, product, SaaS, app, platform, or enterprise.
           - Crucial Edge Case: Brands named after their founders, creators, or owners (e.g., "Louis Vuitton", "McDonald's", "Ford", "Versace", "Jack Daniel's", "Dyson", "Dell", "Disney", "Chanel", "Porsche") are VALID companies.
           - Entity type must be 'company'. 'is_valid' must be true.
           
        2. AMBIGUOUS ('ambiguous'):
           - Input mentions BOTH a person/founder AND the company/brand together (e.g., "Elon Musk's SpaceX", "Steve Jobs' Apple", "Mark Zuckerberg's Meta", "Kylie Jenner's Kylie Cosmetics").
           - You must extract the company/brand portion (e.g., "SpaceX", "Apple", "Meta", "Kylie Cosmetics") and provide it in 'suggested_correction'.
           - Entity type must be 'ambiguous'. 'is_valid' must be true.
           
        3. INVALID ('person', 'government', 'other'):
           - Pure individuals without associated company context in the query string itself (e.g., "Elon Musk", "Taylor Swift", "Narendra Modi", "LeBron James", "Bill Gates") are INVALID.
           - Government bodies, departments, or countries (e.g., "US Government", "IRS", "India") are INVALID unless they function as corporate commercial brands.
           - Entity type must be the category ('person', 'government', 'other'). 'is_valid' must be false.
           
        Evaluate the input string '{input_name}'.
        Return a JSON object with the following fields:
        - "is_valid": boolean (true if it represents a valid or auto-correctable entity, false otherwise)
        - "entity_type": string ("company", "person", "government", "ambiguous", or "other")
        - "reason": string (a concise, single-sentence explanation of the validation choice)
        - "suggested_correction": string or null (if entity_type is 'ambiguous', provide the extracted company name, else null)
        
        Do not output any markdown formatting, explanation, or thinking blocks outside the JSON block.
    """)
    
    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=key,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        prompt = ChatPromptTemplate.from_messages([("user", prompt_text)])
        chain = prompt | llm
        response = chain.invoke({"input_name": company_name})
        
        result = json.loads(response.content)
        # Ensure schema completeness
        if "is_valid" not in result:
            result["is_valid"] = True
        if "entity_type" not in result:
            result["entity_type"] = "company"
        if "reason" not in result:
            result["reason"] = "Default validation outcome."
        if "suggested_correction" not in result:
            result["suggested_correction"] = None
            
        return result
    except Exception as e:
        print(f"Entity validator exception (failing open): {e}")
        # Fail open
        return {
            "is_valid": True,
            "entity_type": "company",
            "reason": f"Validator fallback triggered: {str(e)}",
            "suggested_correction": None
        }
