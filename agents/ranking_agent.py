import logging
from database import db
from services import llm_service
from prompts.ranking_prompt import CANDIDATE_RANKING_PROMPT, CROSS_JOB_COMPARISON_PROMPT

logger = logging.getLogger(__name__)

def get_ranked_candidates(job_id: int) -> list:
    """
    Returns candidates with their screening results sorted by overall_score descending.
    """
    candidates = db.get_candidates_by_job(job_id)
    ranked_candidates = []
    
    for candidate in candidates:
        screening = db.get_screening_result(candidate["id"])
        cand_assess = db.get_candidate_assessment(candidate["id"])
        interview = db.get_candidate_interview(candidate["id"])
        
        # Combine candidate, screening result, assessment, and interview details
        item = {
            "id": candidate["id"],
            "name": candidate["name"],
            "email": candidate["email"],
            "skills": candidate["skills"],
            "experience_years": candidate["experience_years"],
            "resume_filename": candidate["resume_filename"],
            
            # Screening scores
            "skills_score": screening["skills_score"] if screening else 0.0,
            "experience_score": screening["experience_score"] if screening else 0.0,
            "projects_score": screening["projects_score"] if screening else 0.0,
            "education_score": screening["education_score"] if screening else 0.0,
            "overall_score": screening["overall_score"] if screening else 0.0,
            "recommendation": screening["recommendation"] if screening else "Consider",
            "summary": screening["summary"] if screening else "",
            
            # Assessment scores
            "assessment_status": cand_assess["status"] if cand_assess else "None",
            "assessment_score": cand_assess["assessment_score"] if cand_assess and cand_assess["status"] == "completed" else None,
            "final_score": cand_assess["final_score"] if cand_assess and cand_assess["status"] == "completed" else None,
            "final_recommendation": cand_assess["final_recommendation"] if cand_assess and cand_assess["status"] == "completed" else None,
            
            # Interview scores
            "interview_status": interview["status"] if interview else "None",
            "interview_score": interview["score"] if interview and interview["status"] == "completed" else None,
            "interview_recommendation": interview["recommendation"] if interview and interview["status"] == "completed" else None
        }
        ranked_candidates.append(item)
        
    def sort_key(c):
        # Sort key logic: prioritize final combined assessment score, fallback to interview score, fallback to resume score
        if c["final_score"] is not None:
            return c["final_score"]
        if c["interview_score"] is not None:
            return c["interview_score"]
        return c["overall_score"]
        
    ranked_candidates.sort(key=sort_key, reverse=True)
    return ranked_candidates

def get_cross_job_ranked_candidates() -> list:
    """
    Returns all candidates across all job openings with combined scores.
    """
    candidates = db.get_all_candidates_cross_job()
    ranked_candidates = []
    
    for candidate in candidates:
        screening = db.get_screening_result(candidate["id"])
        cand_assess = db.get_candidate_assessment(candidate["id"])
        interview = db.get_candidate_interview(candidate["id"])
        
        item = {
            "id": candidate["id"],
            "name": candidate["name"],
            "email": candidate["email"],
            "skills": candidate["skills"],
            "experience_years": candidate["experience_years"],
            "resume_filename": candidate["resume_filename"],
            "job_title": candidate["job_title"],
            "job_id": candidate["job_id"],
            
            # Screening scores
            "skills_score": screening["skills_score"] if screening else 0.0,
            "experience_score": screening["experience_score"] if screening else 0.0,
            "projects_score": screening["projects_score"] if screening else 0.0,
            "education_score": screening["education_score"] if screening else 0.0,
            "overall_score": screening["overall_score"] if screening else 0.0,
            "recommendation": screening["recommendation"] if screening else "Consider",
            "summary": screening["summary"] if screening else "",
            
            # Assessment scores
            "assessment_status": cand_assess["status"] if cand_assess else "None",
            "assessment_score": cand_assess["assessment_score"] if cand_assess and cand_assess["status"] == "completed" else None,
            "final_score": cand_assess["final_score"] if cand_assess and cand_assess["status"] == "completed" else None,
            "final_recommendation": cand_assess["final_recommendation"] if cand_assess and cand_assess["status"] == "completed" else None,
            
            # Interview scores
            "interview_status": interview["status"] if interview else "None",
            "interview_score": interview["score"] if interview and interview["status"] == "completed" else None,
            "interview_recommendation": interview["recommendation"] if interview and interview["status"] == "completed" else None
        }
        ranked_candidates.append(item)
        
    def sort_key(c):
        if c["final_score"] is not None:
            return c["final_score"]
        if c["interview_score"] is not None:
            return c["interview_score"]
        return c["overall_score"]
        
    ranked_candidates.sort(key=sort_key, reverse=True)
    return ranked_candidates

def generate_ranking_report(job_id: int) -> str:
    """
    Uses AI to generate a comparative ranking report for all screened candidates of a job.
    """
    job = db.get_job(job_id)
    if not job:
        raise ValueError("Job not found")
        
    candidates = get_ranked_candidates(job_id)
    if not candidates:
        return "No candidates found for this job description yet."
        
    candidates_list_str = ""
    for idx, c in enumerate(candidates, 1):
        candidates_list_str += (
            f"{idx}. {c['name']} (Overall Score: {c['overall_score']:.1f}/100)\n"
            f"   - Experience: {c['experience_years']} years\n"
            f"   - Skills Match Score: {c['skills_score']:.1f}\n"
            f"   - Recruiter Recommendation: {c['recommendation']}\n"
            f"   - Summary: {c['summary']}\n"
            f"   - Assessment Status: {c['assessment_status']}"
        )
        if c['final_score'] is not None:
            candidates_list_str += f" (Test Score: {c['assessment_score']:.1f}, Final Score: {c['final_score']:.1f})\n"
        else:
            candidates_list_str += "\n"
            
    variables = {
        "job_title": job["title"],
        "job_skills": ", ".join(job["required_skills"]),
        "job_experience_years": job["experience_years"],
        "candidates_list": candidates_list_str
    }
    
    logger.info("Generating comparative candidate ranking report via AI...")
    try:
        report = llm_service.invoke_llm(CANDIDATE_RANKING_PROMPT, variables)
        return report
    except Exception as e:
        logger.error(f"Failed to generate ranking report: {e}")
        return "Error generating AI comparative ranking report. Please see candidate list details."

def generate_cross_job_comparison_report(candidate_ids: list) -> str:
    """
    Generates a Principal AI comparative report across multiple selected candidates across different roles.
    """
    candidates_info = []
    for cid in candidate_ids:
        candidate = db.get_candidate(cid)
        if not candidate:
            continue
        job = db.get_job(candidate["job_id"])
        screening = db.get_screening_result(cid)
        cand_assess = db.get_candidate_assessment(cid)
        interview = db.get_candidate_interview(cid)
        
        info = (
            f"- **Candidate**: {candidate['name']}\n"
            f"  - **Applied Job**: {job['title'] if job else 'Unknown'}\n"
            f"  - **Experience**: {candidate['experience_years']} years\n"
            f"  - **Skills**: {', '.join(candidate['skills'])}\n"
            f"  - **Resume Screening Score**: {screening['overall_score'] if screening else 0.0}/100\n"
            f"  - **Assessment Test Score**: {cand_assess['assessment_score'] if cand_assess and cand_assess['status'] == 'completed' else 'N/A'}/100\n"
            f"  - **AI Interview Score**: {interview['score'] if interview and interview['status'] == 'completed' else 'N/A'}/100\n"
            f"  - **Screening Summary**: {screening['summary'] if screening else 'N/A'}\n"
            f"  - **Strengths**: {', '.join(screening['strengths']) if screening else 'N/A'}\n"
            f"  - **Weaknesses**: {', '.join(screening['weaknesses']) if screening else 'N/A'}\n"
        )
        candidates_info.append(info)
        
    if not candidates_info:
        return "Please select valid candidates to perform cross-job analysis."
        
    variables = {
        "candidates_to_compare": "\n".join(candidates_info)
    }
    
    logger.info("Invoking AI for cross-job candidate benchmark analysis...")
    try:
        report = llm_service.invoke_llm(CROSS_JOB_COMPARISON_PROMPT, variables)
        return report
    except Exception as e:
        logger.error(f"Failed to generate cross-job report: {e}")
        return "Error occurred while generating Principal AI Cross-Job Comparison report."
