import logging
import json
from database import db
from services import llm_service, assessment_service
from prompts.interview_prompt import INTERVIEW_GENERATION_PROMPT, INTERVIEW_EVALUATION_PROMPT

logger = logging.getLogger(__name__)

def generate_candidate_interview(candidate_id: int, force_regenerate: bool = False) -> str:
    """
    Generates a personalized 5-question interview targeting the candidate's screening weaknesses,
    stores it in the database, and returns the generated access token.
    """
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found.")

    job = db.get_job(candidate["job_id"])
    if not job:
        raise ValueError(f"Job for candidate {candidate_id} not found.")

    screening = db.get_screening_result(candidate_id)
    if not screening:
        raise ValueError(f"Candidate {candidate_id} must be screened first.")

    # Check if interview already exists
    if not force_regenerate:
        existing = db.get_candidate_interview(candidate_id)
        if existing:
            return existing["token"]

    # Generate custom interview questions targeting weaknesses
    logger.info(f"Generating custom interview questions for {candidate['name']} targeting gaps...")
    
    variables = {
        "candidate_id": candidate_id,
        "candidate_name": candidate["name"],
        "job_title": job["title"],
        "job_skills": ", ".join(job["required_skills"]),
        "job_description": job["description"],
        "candidate_skills": ", ".join(candidate["skills"]),
        "candidate_experience_years": candidate["experience_years"],
        "screening_summary": screening["summary"],
        "screening_strengths": ", ".join(screening["strengths"]),
        "screening_weaknesses": ", ".join(screening["weaknesses"])
    }

    try:
        res = llm_service.generate_json(INTERVIEW_GENERATION_PROMPT, variables)
        questions = res.get("questions", [])
    except Exception as e:
        logger.error(f"Failed to generate custom interview questions: {e}")
        # Fallback questions targeting generic fit
        questions = [
            {"id": "int_1", "topic": "Experience & Role Fit", "question": f"Describe your past experience working as a {job['title']} and how it aligns with this opening."},
            {"id": "int_2", "topic": "Technical Architecture", "question": "Explain a complex architectural challenge you faced in your last project and how you solved it."},
            {"id": "int_3", "topic": "Core Technologies", "question": f"How do you keep up with updates and best practices in technologies like {', '.join(job['required_skills'][:3])}?"},
            {"id": "int_4", "topic": "Problem Solving", "question": "Walk us through your typical process for debugging a memory leak or a critical production issue."},
            {"id": "int_5", "topic": "Collaboration", "question": "Describe a situation where you had a technical disagreement with a colleague. How did you resolve it?"}
        ]

    # Generate token
    token = assessment_service.generate_assessment_token()
    db.create_candidate_interview(
        candidate_id=candidate_id,
        token=token,
        questions=questions
    )
    return token

def evaluate_candidate_interview(candidate_id: int):
    """
    Evaluates the candidate's interview responses using AI and saves the scores/recommendation.
    """
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate {candidate_id} not found.")

    job = db.get_job(candidate["job_id"])
    if not job:
        raise ValueError(f"Job for candidate {candidate_id} not found.")

    interview = db.get_candidate_interview(candidate_id)
    if not interview:
        raise ValueError(f"No interview found for candidate {candidate_id}.")

    if interview["status"] != "completed":
        raise ValueError(f"Interview is not in completed state. Status: {interview['status']}")

    logger.info(f"AI Evaluating interview responses for candidate: {candidate['name']}...")

    variables = {
        "job_title": job["title"],
        "candidate_name": candidate["name"],
        "interview_questions": json.dumps(interview["questions"], indent=2),
        "candidate_responses": json.dumps(interview["responses"], indent=2)
    }

    try:
        evaluation = llm_service.generate_json(INTERVIEW_EVALUATION_PROMPT, variables)
    except Exception as e:
        logger.error(f"Failed to evaluate candidate interview: {e}")
        evaluation = {
            "score": 60.0,
            "summary": "AI Evaluation timed out or failed. Please review candidate responses manually.",
            "strengths": ["Review pending"],
            "weaknesses": ["Review pending"],
            "ai_review": "Failed to automatically evaluate responses using LLM due to an error.",
            "recommendation": "Consider"
        }

    score = float(evaluation.get("score", 60.0))
    summary = evaluation.get("summary", "Evaluation pending.")
    strengths = evaluation.get("strengths", [])
    weaknesses = evaluation.get("weaknesses", [])
    ai_review = evaluation.get("ai_review", "Evaluation pending.")
    recommendation = evaluation.get("recommendation", "Consider")

    db.update_candidate_interview_evaluation(
        candidate_id=candidate_id,
        score=score,
        summary=summary,
        strengths=strengths,
        weaknesses=weaknesses,
        ai_review=ai_review,
        recommendation=recommendation
    )
