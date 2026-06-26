from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Assessment(BaseModel):
    id: Optional[int] = None
    job_id: int
    title: str
    questions: List[Dict[str, Any]] = Field(default_factory=list) # Structure: [{"type": "mcq", "question": "...", "options": [...], "answer": "..."}, ...]
    created_at: Optional[str] = None

class CandidateAssessment(BaseModel):
    id: Optional[int] = None
    candidate_id: int
    assessment_id: int
    token: str
    status: str = "pending" # pending, completed
    responses: Optional[Dict[str, Any]] = None # Structure: {"q_0": "candidate response", ...}
    technical_score: Optional[float] = None
    problem_solving_score: Optional[float] = None
    communication_score: Optional[float] = None
    assessment_score: Optional[float] = None
    ai_review: Optional[str] = None
    final_score: Optional[float] = None
    final_recommendation: Optional[str] = None # Strong Hire, Hire, Consider, Reject
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
