from pydantic import BaseModel, Field
from typing import List, Optional

class Candidate(BaseModel):
    id: Optional[int] = None
    job_id: int
    name: str
    email: str
    skills: List[str] = Field(default_factory=list)
    experience_years: float
    education: str
    projects: str
    resume_filename: Optional[str] = None
    resume_path: Optional[str] = None
    created_at: Optional[str] = None
