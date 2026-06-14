from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    company_name: str
    analysis_type: str
    raw_bullets: Optional[str]
    final_report: Optional[str]
    validation_status: Optional[str]
    retry_count: Optional[int]
    data_sufficient: Optional[bool]
    search_queries: Optional[List[str]]
    validation_summary: Optional[str]
    critic_feedback: Optional[str]
    revision_count: Optional[int]
    needs_retry: Optional[bool]
    critic_passes: Optional[bool]

