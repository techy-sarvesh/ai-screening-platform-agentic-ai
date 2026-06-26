def calculate_overall_resume_score(skills_score: float, experience_score: float, projects_score: float, education_score: float) -> float:
    """
    Overall Score = 40% Skills + 30% Experience + 20% Projects + 10% Education
    """
    score = (
        (skills_score * 0.40) +
        (experience_score * 0.30) +
        (projects_score * 0.20) +
        (education_score * 0.10)
    )
    return round(score, 2)

def calculate_final_hiring_score(resume_score: float, assessment_score: float) -> float:
    """
    Final Score = 70% Resume Score + 30% Assessment Score
    """
    score = (resume_score * 0.70) + (assessment_score * 0.30)
    return round(score, 2)

def get_recommendation_label(final_score: float) -> str:
    """
    Returns hiring recommendation text.
    """
    if final_score >= 85.0:
        return "Strong Hire"
    elif final_score >= 70.0:
        return "Hire"
    elif final_score >= 55.0:
        return "Consider"
    else:
        return "Reject"
