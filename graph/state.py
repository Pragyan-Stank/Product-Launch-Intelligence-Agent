from typing import TypedDict, Optional

class AgentState(TypedDict):
    company_name: str
    analysis_type: str
    raw_bullets: Optional[str]
    final_report: Optional[str]
    validation_status: Optional[str]
