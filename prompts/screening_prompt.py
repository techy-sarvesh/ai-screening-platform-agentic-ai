RESUME_EXTRACTION_PROMPT = """You are an expert AI resume parser. Parse the following candidate resume text and extract the details as a valid JSON object.

Extract:
- name: Candidate's full name (string)
- email: Candidate's email address (string)
- skills: List of skills/technologies mentioned (list of strings)
- experience_years: Estimated years of professional experience (float/integer). Look closely at work dates. If not mentioned, estimate based on roles or use 0.
- education: Summary of education, degrees, university (string)
- projects: Summary of projects, achievements, and responsibilities (string)

Return ONLY a valid JSON object. Do not include markdown formatting or explanation outside the JSON.

Resume Text:
{resume_text}
"""

RESUME_SCREENING_PROMPT = """You are an AI Screening Agent. Evaluate the Candidate Profile against the Job Description and requirements.

Job Description:
Title: {job_title}
Experience Required: {job_experience_years} years
Required Skills: {job_skills}
Description: {job_description}

Candidate Profile:
Name: {candidate_name}
Skills: {candidate_skills}
Experience Years: {candidate_experience_years}
Education: {candidate_education}
Projects: {candidate_projects}

Analyze:
1. **Skill Match**: Compare candidate skills with required job skills. Provide a skill match score from 0 to 100 representing what percentage of key required skills are met. Explain your calculation.
2. **Experience Match**: Compare candidate experience with required job experience. Provide an experience match score from 0 to 100. (e.g. If required is 5 years, and candidate has 4 years, score is 80%. If candidate has >= required, score is 100%). Explain your calculation.
3. **Projects Score**: Score the relevance of candidate projects to the job requirements (0 to 100).
4. **Education Score**: Score the relevance of candidate education to the job requirements (0 to 100).
5. **Recruiter Summary**: Provide a short, recruiter-friendly summary of the candidate's fit.
6. **Strengths**: List 2-5 key strengths of this candidate for this job.
7. **Weaknesses**: List 1-4 key weaknesses or missing areas.
8. **Recommendation**: Recommend either "Proceed to Assessment" (if matching score is reasonable and assessment is enabled), "Consider", or "Reject".

Your output MUST be a valid JSON object with the following keys. Return ONLY the JSON object.

JSON Schema:
{{
  "skills_score": 0.0,
  "skills_match_explanation": "string details...",
  "experience_score": 0.0,
  "experience_match_explanation": "string details...",
  "projects_score": 0.0,
  "education_score": 0.0,
  "summary": "string summary...",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "recommendation": "Proceed to Assessment | Consider | Reject"
}}
"""

JOB_DESCRIPTION_EXTRACTION_PROMPT = """You are an expert AI Job Planner. Analyze the following document text (which is a Job Description or a sample candidate resume) and extract the job requirements parameters.

Extract:
- title: Recommended or parsed Job Title (string)
- description: Recommended Job Description summary detailing primary duties and qualifications (string)
- required_skills: Recommended list of 4-10 key technical skills/technologies required for this role (list of strings)
- experience_years: Estimated/recommended number of years of experience required (integer)

Return ONLY a valid JSON object. Do not include markdown formatting or explanation outside the JSON.

Document Text:
{document_text}
"""
