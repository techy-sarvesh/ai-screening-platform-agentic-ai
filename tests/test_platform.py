import pytest
import os
import sys

# Add workspace directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import db
from services import scoring_service, assessment_service

@pytest.fixture(autouse=True)
def setup_db():
    # Setup test database path (independent of main db)
    test_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_sqlite.db"))
    db.DB_PATH = test_db_path
    db.init_db()
    yield
    # Cleanup after test runs
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_database_job_crud():
    # 1. Create a job
    job_id = db.create_job(
        title="Test Developer",
        description="Write tests all day",
        required_skills=["pytest", "python"],
        experience_years=2,
        assessment_required=True
    )
    assert job_id > 0
    
    # 2. Retrieve the job
    job = db.get_job(job_id)
    assert job is not None
    assert job["title"] == "Test Developer"
    assert "pytest" in job["required_skills"]
    assert job["experience_years"] == 2
    assert job["assessment_required"] is True

def test_database_candidate_crud():
    # 1. Create a job
    job_id = db.create_job(
        title="Test Developer",
        description="Write tests all day",
        required_skills=["pytest"],
        experience_years=2,
        assessment_required=True
    )
    
    # 2. Create candidate
    candidate_id = db.create_candidate(
        job_id=job_id,
        name="Alice Jenkins",
        email="alice@test.com",
        skills=["pytest", "python"],
        experience_years=3.5,
        education="B.S. Computer Science",
        projects="Automated testing suite project",
        resume_filename="alice_resume.pdf",
        resume_path="/path/to/alice_resume.pdf"
    )
    assert candidate_id > 0
    
    # 3. Get candidate
    candidate = db.get_candidate(candidate_id)
    assert candidate is not None
    assert candidate["name"] == "Alice Jenkins"
    assert candidate["email"] == "alice@test.com"
    assert "pytest" in candidate["skills"]
    assert candidate["experience_years"] == 3.5

def test_scoring_formulas():
    # Test resume scoring logic: 40% Skills + 30% Experience + 20% Projects + 10% Education
    res_score = scoring_service.calculate_overall_resume_score(
        skills_score=80.0,
        experience_score=70.0,
        projects_score=90.0,
        education_score=100.0
    )
    # Calculation: (80*0.4)+(70*0.3)+(90*0.2)+(100*0.1) = 32 + 21 + 18 + 10 = 81
    assert res_score == 81.0
    
    # Test final hiring score: 70% Resume + 30% Assessment
    final = scoring_service.calculate_final_hiring_score(
        resume_score=80.0,
        assessment_score=90.0
    )
    # Calculation: (80*0.7) + (90*0.3) = 56 + 27 = 83
    assert final == 83.0
    
    # Test recommendation labels
    assert scoring_service.get_recommendation_label(85.0) == "Strong Hire"
    assert scoring_service.get_recommendation_label(75.0) == "Hire"
    assert scoring_service.get_recommendation_label(60.0) == "Consider"
    assert scoring_service.get_recommendation_label(50.0) == "Reject"

def test_assessment_token_and_links():
    token = assessment_service.generate_assessment_token()
    assert len(token) == 32 # MD5/hex character length of UUID
    
    url = assessment_service.generate_assessment_url("http://example.com/", token)
    assert url == f"http://example.com/test/{token}"

def test_interview_db_operations():
    # 1. Create a job and candidate
    job_id = db.create_job(
        title="Test Developer",
        description="Write tests all day",
        required_skills=["pytest"],
        experience_years=2,
        assessment_required=True
    )
    
    candidate_id = db.create_candidate(
        job_id=job_id,
        name="Charlie Brown",
        email="charlie@test.com",
        skills=["python"],
        experience_years=2.0,
        education="High School",
        projects="Comic strip maker",
        resume_filename="charlie.pdf",
        resume_path="/path/to/charlie.pdf"
    )
    
    # 2. Add an interview
    token = "interview_token_charlie"
    questions = [
        {"id": "int_1", "topic": "Python testing", "question": "Explain pytest fixtures."}
    ]
    interview_id = db.create_candidate_interview(
        candidate_id=candidate_id,
        token=token,
        questions=questions
    )
    assert interview_id > 0
    
    # 3. Retrieve interview
    interview = db.get_candidate_interview(candidate_id)
    assert interview is not None
    assert interview["token"] == token
    assert interview["status"] == "pending"
    assert interview["questions"][0]["topic"] == "Python testing"
    
    # 4. Submit responses
    responses = {"int_1": "Fixtures are functions that feed data or setup/teardown code to tests."}
    db.submit_candidate_interview_responses(candidate_id, responses)
    
    # 5. Retrieve submitted interview
    interview = db.get_candidate_interview_by_token(token)
    assert interview["status"] == "completed"
    assert interview["responses"]["int_1"] == responses["int_1"]
    
    # 6. Evaluate interview
    db.update_candidate_interview_evaluation(
        candidate_id=candidate_id,
        score=85.0,
        summary="Excellent testing fundamentals.",
        strengths=["Clear explanation of fixtures"],
        weaknesses=["None noted"],
        ai_review="Candidate understands pytest fixtures clearly.",
        recommendation="Strong Hire"
    )
    
    # Verify final assessment details
    interview = db.get_candidate_interview(candidate_id)
    assert interview["score"] == 85.0
    assert "Clear explanation of fixtures" in interview["strengths"]
    assert interview["recommendation"] == "Strong Hire"

def test_cross_job_candidate_retrieval():
    # 1. Create two jobs
    job_id_1 = db.create_job("iOS Developer", "Build iOS apps", ["Swift"], 3, True)
    job_id_2 = db.create_job("Android Developer", "Build Android apps", ["Kotlin"], 3, True)
    
    # 2. Create candidates for each
    db.create_candidate(job_id_1, "John iOS", "john@ios.com", ["Swift", "UIKit"], 4, "B.S.", "iOS app", "resume1.pdf", "/p1")
    db.create_candidate(job_id_2, "Andy Android", "andy@android.com", ["Kotlin", "Compose"], 5, "B.S.", "Android app", "resume2.pdf", "/p2")
    
    # 3. Fetch cross-job
    candidates = db.get_all_candidates_cross_job()
    assert len(candidates) >= 2
    
    # Extract names and verify
    names = [c["name"] for c in candidates]
    assert "John iOS" in names
    assert "Andy Android" in names
    
    # Verify job titles are attached
    ios_cand = [c for c in candidates if c["name"] == "John iOS"][0]
    assert ios_cand["job_title"] == "iOS Developer"
    
    android_cand = [c for c in candidates if c["name"] == "Andy Android"][0]
    assert android_cand["job_title"] == "Android Developer"

def test_interview_regeneration():
    from agents.interview_agent import generate_candidate_interview
    
    # 1. Create job, candidate, and screening results first (needed for interview generation)
    job_id = db.create_job("Developer", "Desc", ["Python"], 2, True)
    candidate_id = db.create_candidate(job_id, "Regen User", "r@test.com", ["Python"], 2, "B.S.", "Proj", "res.pdf", "/p")
    db.create_screening_result(
        candidate_id=candidate_id,
        skills_score=80.0,
        experience_score=80.0,
        projects_score=80.0,
        education_score=80.0,
        overall_score=80.0,
        skills_match_explanation="Ok",
        experience_match_explanation="Ok",
        summary="Ok",
        strengths=["Python"],
        weaknesses=["None"],
        recommendation="Hire"
    )
    
    # 2. Generate first interview
    token_1 = generate_candidate_interview(candidate_id, force_regenerate=False)
    assert token_1 is not None
    
    # Check that calling it again without force_regenerate returns the same token
    token_2 = generate_candidate_interview(candidate_id, force_regenerate=False)
    assert token_2 == token_1
    
    # Check that calling it with force_regenerate returns a new token (or overwrites it)
    token_3 = generate_candidate_interview(candidate_id, force_regenerate=True)
    assert token_3 != token_1

