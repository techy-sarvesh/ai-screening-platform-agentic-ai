import logging
import json
from database import db
from services import llm_service, scoring_service
from prompts.assessment_prompt import ASSESSMENT_GENERATION_PROMPT, ASSESSMENT_EVALUATION_PROMPT

logger = logging.getLogger(__name__)

def generate_and_save_assessment(job_id: int) -> int:
    """
    Generates a technical test template for a job using AI and stores it in the database.
    """
    job = db.get_job(job_id)
    if not job:
        raise ValueError(f"Job with ID {job_id} not found.")

    logger.info(f"Generating technical assessment template for job: {job['title']}...")
    variables = {
        "job_title": job["title"],
        "job_skills": ", ".join(job["required_skills"])
    }

    try:
        assessment_data = llm_service.generate_json(ASSESSMENT_GENERATION_PROMPT, variables)
    except Exception as e:
        logger.error(f"Failed to generate assessment template: {e}")
        # Return fallback questions
        assessment_data = {
            "title": f"Technical Assessment for {job['title']}",
            "questions": [
                {
                    "id": "q_1",
                    "section": "Core Skills",
                    "type": "mcq",
                    "question": f"Which of the following is most commonly used when working with {job['required_skills'][0] if job['required_skills'] else 'this role'}?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A"
                },
                {
                    "id": "q_2",
                    "section": "Fundamentals",
                    "type": "short_answer",
                    "question": f"Describe the main architecture patterns recommended for development in {job['title']}.",
                    "correct_answer_guideline": "Should mention standard patterns and frameworks."
                },
                {
                    "id": "q_3",
                    "section": "Coding",
                    "type": "coding",
                    "question": "Write a function to verify if an input string is a valid email address.",
                    "starter_code": "def is_valid_email(email: str) -> bool:\n    # Write code here\n    pass",
                    "correct_answer_guideline": "Correct regular expression or email validation checks."
                }
            ]
        }

    title = assessment_data.get("title", f"Technical Assessment for {job['title']}")
    questions = assessment_data.get("questions", [])

    assessment_id = db.create_assessment(
        job_id=job_id,
        title=title,
        questions=questions
    )
    return assessment_id

def evaluate_candidate_test(candidate_id: int):
    """
    Grades the candidate's assessment responses using AI, calculates the combined
    Final hiring score and recommendation, and stores the results in the database.
    """
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        raise ValueError(f"Candidate with ID {candidate_id} not found.")

    screening = db.get_screening_result(candidate_id)
    if not screening:
        raise ValueError(f"Candidate {candidate_id} has not been screened yet.")

    cand_assess = db.get_candidate_assessment(candidate_id)
    if not cand_assess:
        raise ValueError(f"Candidate {candidate_id} has not been assigned any assessment.")

    if cand_assess["status"] != "completed":
        raise ValueError(f"Candidate assessment is not in 'completed' status. Current: {cand_assess['status']}")

    assessment = db.get_assessment(cand_assess["assessment_id"])
    if not assessment:
        raise ValueError(f"Assessment template ID {cand_assess['assessment_id']} not found.")

    # 1. Prepare inputs for AI evaluation
    test_questions_str = json.dumps(assessment["questions"], indent=2)
    candidate_responses_str = json.dumps(cand_assess["responses"], indent=2)

    logger.info(f"AI Grading assessment responses for candidate: {candidate['name']}...")
    job = db.get_job(candidate["job_id"])
    
    variables = {
        "job_title": job["title"] if job else "Software Engineer",
        "job_skills": ", ".join(job["required_skills"]) if job else "Coding",
        "test_questions": test_questions_str,
        "candidate_responses": candidate_responses_str
    }

    try:
        evaluation = llm_service.generate_json(ASSESSMENT_EVALUATION_PROMPT, variables)
    except Exception as e:
        logger.error(f"Failed to evaluate candidate responses: {e}")
        evaluation = {
            "technical_score": 6.0,
            "problem_solving_score": 6.0,
            "communication_score": 6.0,
            "assessment_score": 60.0,
            "ai_review": "Failed to automatically evaluate responses using LLM due to an error. Manual grading is suggested.",
            "recommendation": "Consider"
        }

    # Extract score details
    technical_score = float(evaluation.get("technical_score", 5.0))
    problem_solving_score = float(evaluation.get("problem_solving_score", 5.0))
    communication_score = float(evaluation.get("communication_score", 5.0))
    assessment_score = float(evaluation.get("assessment_score", 50.0))
    ai_review = evaluation.get("ai_review", "Evaluation pending.")

    # 2. Calculate Final Combined Score
    # Final Score = 70% Resume Score + 30% Assessment Score
    resume_score = screening["overall_score"]
    final_score = scoring_service.calculate_final_hiring_score(
        resume_score=resume_score,
        assessment_score=assessment_score
    )

    # 3. Determine final hiring recommendation
    final_recommendation = scoring_service.get_recommendation_label(final_score)

    # 4. Save results to the Database
    db.update_candidate_assessment_evaluation(
        candidate_id=candidate_id,
        technical_score=technical_score,
        problem_solving_score=problem_solving_score,
        communication_score=communication_score,
        assessment_score=assessment_score,
        ai_review=ai_review,
        final_score=final_score,
        final_recommendation=final_recommendation
    )
