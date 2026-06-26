INTERVIEW_GENERATION_PROMPT = """You are an expert technical interviewer. Design a customized interview for the candidate "{candidate_name}" who applied for the job "{job_title}".

Job Details:
Title: {job_title}
Required Skills: {job_skills}
Description: {job_description}

Candidate Profile:
Extracted Skills: {candidate_skills}
Experience Years: {candidate_experience_years}
Screening Summary: {screening_summary}
Screening Strengths: {screening_strengths}
Screening Weaknesses/Concerns: {screening_weaknesses}

Generate exactly 5 custom interview questions. The questions must be tailored to this candidate:
- At least 2 questions should target the candidate's screening weaknesses or missing skills, testing if they can learn, have alternative knowledge, or how they handle those gaps.
- At least 1 question should probe their listed project experience and responsibilities.
- The remaining questions should test standard concepts for the role and behavioral fit.

Your output MUST be a valid JSON object matching the schema below. Return ONLY the JSON object. Do not include markdown formatting or extra text outside the JSON.

JSON Schema:
{{
  "candidate_id": {candidate_id},
  "questions": [
    {{
      "id": "int_1",
      "topic": "string - e.g. Combine framework gap / Projects",
      "question": "string - the question text to ask the candidate"
    }}
  ]
}}
"""

INTERVIEW_EVALUATION_PROMPT = """You are an expert AI Interview Evaluator. Grade the Candidate's responses to the custom interview.

Job Title: {job_title}
Candidate: {candidate_name}

Interview Questions:
{interview_questions}

Candidate Responses:
{candidate_responses}

Evaluate each response. Score the overall interview performance from 0 to 100 based on technical depth, accuracy, project explanation, and fit.

Your output MUST be a valid JSON object matching the schema below. Return ONLY the JSON object.

JSON Schema:
{{
  "score": 0.0,
  "summary": "string - general summary of how the candidate performed...",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "ai_review": "string - detailed review of the candidate's answers and technical competence...",
  "recommendation": "Strong Hire | Hire | Consider | Reject"
}}
"""
