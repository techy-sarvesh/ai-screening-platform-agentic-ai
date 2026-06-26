from pydantic import BaseModel, Field
from typing import List, Optional

class Job(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    required_skills: List[str] = Field(default_factory=list)
    experience_years: int
    assessment_required: bool = True
    created_at: Optional[str] = None
