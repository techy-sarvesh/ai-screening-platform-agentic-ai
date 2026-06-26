from pydantic import BaseModel, Field
from typing import List, Optional

class ScreeningResult(BaseModel):
    id: Optional[int] = None
    candidate_id: int
    skills_score: float
    experience_score: float
    projects_score: float
    education_score: float
    overall_score: float
    skills_match_explanation: str
    experience_match_explanation: str
    summary: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendation: str
    created_at: Optional[str] = None
