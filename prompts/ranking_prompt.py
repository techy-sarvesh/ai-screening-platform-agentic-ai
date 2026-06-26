CANDIDATE_RANKING_PROMPT = """You are an AI Ranking Agent. Analyze the list of screened candidates for the job "{job_title}" and produce a comparative ranking report explaining the placement.

Job requirements:
Required Skills: {job_skills}
Experience Required: {job_experience_years} years

Screened Candidates:
{candidates_list}

Produce a comparison that explains:
1. Why the top candidates are ranked high.
2. Key differences between the candidates.
3. Recommendations for next steps.

Output format:
Return your response in standard Markdown.
"""

CROSS_JOB_COMPARISON_PROMPT = """You are a Principal AI Talent Architect. Analyze the following candidates who have applied for different roles across our organization and provide a cross-job comparative assessment.

Candidates to Compare:
{candidates_to_compare}

Perform a comprehensive review and output a report covering:
1. **Talent Quality Benchmarking**: Contrast the general technical depth and problem-solving capability of these candidates.
2. **Cross-Role Fitment**: Identify if any candidate would be a better fit for a different open role than the one they applied for (e.g. A Senior iOS candidate showing strong systems skills who could fit a Backend or Tech Lead role, or vice versa).
3. **Strategic Recommendations**: Provide clear advice on which candidates are "must-hires" for the company and what project/team context they would thrive in.

Output format:
Return your response in standard Markdown.
"""
