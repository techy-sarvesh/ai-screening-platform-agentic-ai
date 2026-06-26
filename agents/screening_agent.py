import logging
from database import db
from services import llm_service, scoring_service
from prompts.screening_prompt import RESUME_EXTRACTION_PROMPT, RESUME_SCREENING_PROMPT

logger = logging.getLogger(__name__)

def screen_candidate(resume_text: str, job_id: int, resume_filename: str, resume_path: str) -> int:
    """
    Extracts candidate profile, screens it against job requirements, 
    calculates scores, and stores them in the database.
    Returns the candidate_id of the created candidate.
    """
    # 1. Get Job details
    job = db.get_job(job_id)
    if not job:
        raise ValueError(f"Job with ID {job_id} not found.")

    # 2. Extract Candidate Profile from Resume Text
    logger.info("Extracting candidate profile from resume text using AI...")
    extraction_vars = {"resume_text": resume_text}
    
    try:
        profile = llm_service.generate_json(RESUME_EXTRACTION_PROMPT, extraction_vars)
    except Exception as e:
        logger.error(f"Failed to extract profile: {e}")
        # Fallback profile in case of AI parsing failure
        profile = {
            "name": "Unknown Candidate",
            "email": "unknown@example.com",
            "skills": [],
            "experience_years": 0.0,
            "education": "Not specified",
            "projects": "Not specified"
        }

    # Clean and validate profile fields
    name = profile.get("name", "Unknown Candidate") or "Unknown Candidate"
    email = profile.get("email", "unknown@example.com") or "unknown@example.com"
    skills = profile.get("skills", [])
    if not isinstance(skills, list):
        skills = [skills] if skills else []
    
    try:
        experience_years = float(profile.get("experience_years", 0))
    except (ValueError, TypeError):
        experience_years = 0.0
        
    education = profile.get("education", "Not specified") or "Not specified"
    projects = profile.get("projects", "Not specified") or "Not specified"

    # 3. Create Candidate in Database
    candidate_id = db.create_candidate(
        job_id=job_id,
        name=name,
        email=email,
        skills=skills,
        experience_years=experience_years,
        education=education,
        projects=projects,
        resume_filename=resume_filename,
        resume_path=resume_path
    )

    # 4. Screen Candidate against Job Description
    logger.info(f"Screening candidate {name} against job requirements...")
    screening_vars = {
        "job_title": job["title"],
        "job_experience_years": job["experience_years"],
        "job_skills": ", ".join(job["required_skills"]),
        "job_description": job["description"],
        "candidate_name": name,
        "candidate_skills": ", ".join(skills),
        "candidate_experience_years": experience_years,
        "candidate_education": education,
        "candidate_projects": projects
    }

    try:
        screening_res = llm_service.generate_json(RESUME_SCREENING_PROMPT, screening_vars)
    except Exception as e:
        logger.error(f"Failed to screen candidate: {e}")
        # Fallback screening response
        screening_res = {
            "skills_score": 50.0,
            "skills_match_explanation": "Could not calculate due to LLM timeout.",
            "experience_score": 50.0,
            "experience_match_explanation": "Could not calculate due to LLM timeout.",
            "projects_score": 50.0,
            "education_score": 50.0,
            "summary": "AI Screening timed out, please review manually.",
            "strengths": ["None identified automatically"],
            "weaknesses": ["AI evaluation failed"],
            "recommendation": "Consider"
        }

    # Extract score values
    skills_score = float(screening_res.get("skills_score", 50.0))
    experience_score = float(screening_res.get("experience_score", 50.0))
    projects_score = float(screening_res.get("projects_score", 50.0))
    education_score = float(screening_res.get("education_score", 50.0))
    
    # Calculate Overall Score using our formula:
    # 40% Skills + 30% Experience + 20% Projects + 10% Education
    overall_score = scoring_service.calculate_overall_resume_score(
        skills_score=skills_score,
        experience_score=experience_score,
        projects_score=projects_score,
        education_score=education_score
    )

    skills_match_explanation = screening_res.get("skills_match_explanation", "No details provided.")
    experience_match_explanation = screening_res.get("experience_match_explanation", "No details provided.")
    summary = screening_res.get("summary", "No summary generated.")
    strengths = screening_res.get("strengths", [])
    weaknesses = screening_res.get("weaknesses", [])
    recommendation = screening_res.get("recommendation", "Consider")

    # 5. Create Screening Result in Database
    db.create_screening_result(
        candidate_id=candidate_id,
        skills_score=skills_score,
        experience_score=experience_score,
        projects_score=projects_score,
        education_score=education_score,
        overall_score=overall_score,
        skills_match_explanation=skills_match_explanation,
        experience_match_explanation=experience_match_explanation,
        summary=summary,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendation=recommendation
    )

    return candidate_id
