import os
import logging
from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import db
from agents.assessment_agent import evaluate_candidate_test
from agents.interview_agent import evaluate_candidate_interview

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Candidate Screening Platform API")

# Setup Jinja2 templates directory
templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>AI Screening API</title>
            <style>
                body { font-family: sans-serif; text-align: center; padding-top: 100px; background-color: #0b0f19; color: #f3f4f6; }
                h1 { color: #6366f1; }
            </style>
        </head>
        <body>
            <h1>AI Candidate Screening Platform Backend</h1>
            <p>The API backend is running. Candidate tests and interviews can be accessed via unique tokens.</p>
        </body>
    </html>
    """

# --- ASSESSMENTS ENDPOINTS ---

@app.get("/test/{token}", response_class=HTMLResponse)
async def get_test(token: str, request: Request):
    # 1. Fetch candidate assessment by token
    cand_assess = db.get_candidate_assessment_by_token(token)
    if not cand_assess:
        raise HTTPException(status_code=404, detail="Assessment not found or invalid token.")

    if cand_assess["status"] == "completed":
        candidate = db.get_candidate(cand_assess["candidate_id"])
        name = candidate["name"] if candidate else "Candidate"
        return templates.TemplateResponse(request, "thank_you.html", {
            "title": "Assessment Completed",
            "message": "Thank you for completing your assessment! Your answers have been received and evaluated.",
            "candidate_name": name
        })

    # 2. Fetch job and assessment details
    assessment = db.get_assessment(cand_assess["assessment_id"])
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment template details not found.")

    candidate = db.get_candidate(cand_assess["candidate_id"])
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate details not found.")

    # 3. Render test template
    return templates.TemplateResponse(request, "test_page.html", {
        "token": token,
        "assessment_title": assessment["title"],
        "candidate_name": candidate["name"],
        "candidate_email": candidate["email"],
        "questions": assessment["questions"]
    })

@app.post("/test/{token}/submit", response_class=HTMLResponse)
async def submit_test(token: str, request: Request, background_tasks: BackgroundTasks):
    # 1. Verify token
    cand_assess = db.get_candidate_assessment_by_token(token)
    if not cand_assess:
        raise HTTPException(status_code=404, detail="Assessment not found or invalid token.")

    if cand_assess["status"] == "completed":
        raise HTTPException(status_code=400, detail="Assessment has already been submitted.")

    candidate = db.get_candidate(cand_assess["candidate_id"])
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # 2. Parse form responses
    form_data = await request.form()
    responses = {}
    for key, value in form_data.items():
        if key.startswith("q_"):
            responses[key] = value

    logger.info(f"Received assessment submission from candidate: {candidate['name']}")

    # 3. Store responses & update status to 'completed'
    db.update_candidate_assessment_submission(cand_assess["candidate_id"], responses)

    # 4. Enqueue AI grading in background to prevent client timeout
    background_tasks.add_task(evaluate_candidate_test, cand_assess["candidate_id"])

    # 5. Render Thank You confirmation page
    return templates.TemplateResponse(request, "thank_you.html", {
        "title": "Assessment Submitted",
        "message": "Thank you for submitting your assessment! Your answers have been received and are now being evaluated by our AI team. The hiring manager has been notified.",
        "candidate_name": candidate["name"]
    })

# --- INTERVIEWS ENDPOINTS ---

@app.get("/interview/{token}", response_class=HTMLResponse)
@app.get("/interview/test/{token}", response_class=HTMLResponse)
async def get_interview(token: str, request: Request):
    # 1. Fetch candidate interview by token
    interview = db.get_candidate_interview_by_token(token)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or invalid token.")

    candidate = db.get_candidate(interview["candidate_id"])
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate details not found.")

    if interview["status"] == "completed":
        return templates.TemplateResponse(request, "thank_you.html", {
            "title": "Interview Completed",
            "message": "Thank you for completing your custom AI interview! Your answers are being evaluated.",
            "candidate_name": candidate["name"]
        })

    job = db.get_job(candidate["job_id"])
    job_title = job["title"] if job else "Position"

    # 2. Render interview template
    return templates.TemplateResponse(request, "interview_page.html", {
        "token": token,
        "job_title": job_title,
        "candidate_name": candidate["name"],
        "questions": interview["questions"]
    })

@app.post("/interview/{token}/submit", response_class=HTMLResponse)
@app.post("/interview/test/{token}/submit", response_class=HTMLResponse)
async def submit_interview(token: str, request: Request, background_tasks: BackgroundTasks):
    # 1. Verify token
    interview = db.get_candidate_interview_by_token(token)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or invalid token.")

    if interview["status"] == "completed":
        raise HTTPException(status_code=400, detail="Interview has already been submitted.")

    candidate = db.get_candidate(interview["candidate_id"])
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # 2. Parse form responses
    form_data = await request.form()
    responses = {}
    for key, value in form_data.items():
        if key.startswith("int_"):
            responses[key] = value

    logger.info(f"Received custom interview responses from candidate: {candidate['name']}")

    # 3. Store responses
    db.submit_candidate_interview_responses(interview["candidate_id"], responses)

    # 4. Grade responses in background
    background_tasks.add_task(evaluate_candidate_interview, interview["candidate_id"])

    # 5. Render thank you page
    return templates.TemplateResponse(request, "thank_you.html", {
        "title": "Interview Submitted",
        "message": "Thank you for submitting your custom AI interview responses! Our AI Interview Evaluator is grading your response. The recruiter will view your results shortly.",
        "candidate_name": candidate["name"]
    })
