import sqlite3
import json
import os
from contextlib import contextmanager

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "sqlite.db"))

@contextmanager
def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db_conn() as conn:
        cursor = conn.cursor()
        
        # 1. jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                required_skills TEXT NOT NULL, -- JSON list of skills
                experience_years INTEGER NOT NULL,
                assessment_required INTEGER DEFAULT 1, -- boolean 0/1
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. candidates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                skills TEXT NOT NULL, -- JSON list of skills
                experience_years REAL NOT NULL,
                education TEXT NOT NULL,
                projects TEXT NOT NULL,
                resume_filename TEXT,
                resume_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            )
        """)
        
        # 3. screening_results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER UNIQUE NOT NULL,
                skills_score REAL NOT NULL,
                experience_score REAL NOT NULL,
                projects_score REAL NOT NULL,
                education_score REAL NOT NULL,
                overall_score REAL NOT NULL,
                skills_match_explanation TEXT NOT NULL,
                experience_match_explanation TEXT NOT NULL,
                summary TEXT NOT NULL,
                strengths TEXT NOT NULL, -- JSON list of strings
                weaknesses TEXT NOT NULL, -- JSON list of strings
                recommendation TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
            )
        """)
        
        # 4. assessments table (test templates)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER UNIQUE NOT NULL,
                title TEXT NOT NULL,
                questions TEXT NOT NULL, -- JSON representation of the questions list
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            )
        """)
        
        # 5. candidate_assessments table (instances assigned to candidates)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER UNIQUE NOT NULL,
                assessment_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', -- pending, completed
                responses TEXT, -- JSON structure of questions and candidate answers
                technical_score REAL,
                problem_solving_score REAL,
                communication_score REAL,
                assessment_score REAL,
                ai_review TEXT,
                final_score REAL,
                final_recommendation TEXT,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE,
                FOREIGN KEY (assessment_id) REFERENCES assessments (id) ON DELETE CASCADE
            )
        """)

        # 6. candidate_interviews table (interactive dynamic interviews based on weaknesses)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER UNIQUE NOT NULL,
                token TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', -- pending, completed
                questions TEXT NOT NULL, -- JSON list of questions
                responses TEXT, -- JSON dictionary of responses
                score REAL,
                summary TEXT,
                strengths TEXT, -- JSON list
                weaknesses TEXT, -- JSON list
                ai_review TEXT,
                recommendation TEXT,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
            )
        """)

        # 7. settings table for cross-platform model config
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

# Helper CRUD functions

# --- Settings CRUD ---
def set_setting(key: str, value: str):
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

def get_setting(key: str, default: str = None) -> str:
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row["value"]
            return default
    except Exception:
        return default

# --- Job CRUD ---
def create_job(title: str, description: str, required_skills: list, experience_years: int, assessment_required: bool) -> int:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (title, description, required_skills, experience_years, assessment_required) VALUES (?, ?, ?, ?, ?)",
            (title, description, json.dumps(required_skills), experience_years, 1 if assessment_required else 0)
        )
        return cursor.lastrowid

def get_job(job_id: int) -> dict:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["required_skills"] = json.loads(res["required_skills"])
            res["assessment_required"] = bool(res["assessment_required"])
            return res
        return None

def get_all_jobs() -> list:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
        rows = cursor.fetchall()
        jobs = []
        for row in rows:
            res = dict(row)
            res["required_skills"] = json.loads(res["required_skills"])
            res["assessment_required"] = bool(res["assessment_required"])
            jobs.append(res)
        return jobs

# --- Candidate CRUD ---
def create_candidate(job_id: int, name: str, email: str, skills: list, experience_years: float, education: str, projects: str, resume_filename: str, resume_path: str) -> int:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO candidates (job_id, name, email, skills, experience_years, education, projects, resume_filename, resume_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, name, email, json.dumps(skills), experience_years, education, projects, resume_filename, resume_path)
        )
        return cursor.lastrowid

def get_candidate(candidate_id: int) -> dict:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["skills"] = json.loads(res["skills"])
            return res
        return None

def get_candidates_by_job(job_id: int) -> list:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE job_id = ? ORDER BY id DESC", (job_id,))
        rows = cursor.fetchall()
        candidates = []
        for row in rows:
            res = dict(row)
            res["skills"] = json.loads(res["skills"])
            candidates.append(res)
        return candidates

def get_all_candidates_cross_job() -> list:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, j.title as job_title, j.experience_years as job_experience_years, j.required_skills as job_required_skills
            FROM candidates c
            JOIN jobs j ON c.job_id = j.id
            ORDER BY c.id DESC
        """)
        rows = cursor.fetchall()
        candidates = []
        for row in rows:
            res = dict(row)
            res["skills"] = json.loads(res["skills"])
            res["job_required_skills"] = json.loads(res["job_required_skills"])
            candidates.append(res)
        return candidates

def delete_candidate(candidate_id: int):
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))

# --- Screening Result CRUD ---
def create_screening_result(candidate_id: int, skills_score: float, experience_score: float, projects_score: float, education_score: float, overall_score: float, skills_match_explanation: str, experience_match_explanation: str, summary: str, strengths: list, weaknesses: list, recommendation: str):
    with get_db_conn() as conn:
        cursor = conn.cursor()
        # Clean up existing to ensure unique candidate_id constraints
        cursor.execute("DELETE FROM screening_results WHERE candidate_id = ?", (candidate_id,))
        cursor.execute(
            """INSERT INTO screening_results 
            (candidate_id, skills_score, experience_score, projects_score, education_score, overall_score, skills_match_explanation, experience_match_explanation, summary, strengths, weaknesses, recommendation) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (candidate_id, skills_score, experience_score, projects_score, education_score, overall_score, skills_match_explanation, experience_match_explanation, summary, json.dumps(strengths), json.dumps(weaknesses), recommendation)
        )

def get_screening_result(candidate_id: int) -> dict:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM screening_results WHERE candidate_id = ?", (candidate_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["strengths"] = json.loads(res["strengths"])
            res["weaknesses"] = json.loads(res["weaknesses"])
            return res
        return None

# --- Assessment (Template) CRUD ---
def create_assessment(job_id: int, title: str, questions: list) -> int:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assessments WHERE job_id = ?", (job_id,))
        cursor.execute(
            "INSERT INTO assessments (job_id, title, questions) VALUES (?, ?, ?)",
            (job_id, title, json.dumps(questions))
        )
        return cursor.lastrowid

def get_assessment_by_job(job_id: int) -> dict:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assessments WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["questions"] = json.loads(res["questions"])
            return res
        return None

def get_assessment(assessment_id: int) -> dict:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["questions"] = json.loads(res["questions"])
            return res
        return None

# --- Candidate Assessment CRUD ---
def create_candidate_assessment(candidate_id: int, assessment_id: int, token: str) -> int:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM candidate_assessments WHERE candidate_id = ?", (candidate_id,))
        cursor.execute(
            "INSERT INTO candidate_assessments (candidate_id, assessment_id, token, status) VALUES (?, ?, ?, 'pending')",
            (candidate_id, assessment_id, token)
        )
        return cursor.lastrowid

def get_candidate_assessment(candidate_id: int) -> dict:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidate_assessments WHERE candidate_id = ?", (candidate_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            if res.get("responses"):
                res["responses"] = json.loads(res["responses"])
            return res
        return None

def get_candidate_assessment_by_token(token: str) -> dict:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidate_assessments WHERE token = ?", (token,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            if res.get("responses"):
                res["responses"] = json.loads(res["responses"])
            return res
        return None

def update_candidate_assessment_submission(candidate_id: int, responses: dict):
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE candidate_assessments SET responses = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE candidate_id = ?",
            (json.dumps(responses), candidate_id)
        )

def update_candidate_assessment_evaluation(candidate_id: int, technical_score: float, problem_solving_score: float, communication_score: float, assessment_score: float, ai_review: str, final_score: float, final_recommendation: str):
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE candidate_assessments 
            SET technical_score = ?, problem_solving_score = ?, communication_score = ?, assessment_score = ?, ai_review = ?, final_score = ?, final_recommendation = ? 
            WHERE candidate_id = ?""",
            (technical_score, problem_solving_score, communication_score, assessment_score, ai_review, final_score, final_recommendation, candidate_id)
        )

# --- Candidate Interview CRUD ---
def create_candidate_interview(candidate_id: int, token: str, questions: list) -> int:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM candidate_interviews WHERE candidate_id = ?", (candidate_id,))
        cursor.execute(
            "INSERT INTO candidate_interviews (candidate_id, token, status, questions) VALUES (?, ?, 'pending', ?)",
            (candidate_id, token, json.dumps(questions))
        )
        return cursor.lastrowid

def get_candidate_interview(candidate_id: int) -> dict:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidate_interviews WHERE candidate_id = ?", (candidate_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["questions"] = json.loads(res["questions"])
            if res.get("responses"):
                res["responses"] = json.loads(res["responses"])
            if res.get("strengths"):
                res["strengths"] = json.loads(res["strengths"])
            if res.get("weaknesses"):
                res["weaknesses"] = json.loads(res["weaknesses"])
            return res
        return None

def get_candidate_interview_by_token(token: str) -> dict:
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidate_interviews WHERE token = ?", (token,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res["questions"] = json.loads(res["questions"])
            if res.get("responses"):
                res["responses"] = json.loads(res["responses"])
            if res.get("strengths"):
                res["strengths"] = json.loads(res["strengths"])
            if res.get("weaknesses"):
                res["weaknesses"] = json.loads(res["weaknesses"])
            return res
        return None

def submit_candidate_interview_responses(candidate_id: int, responses: dict):
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE candidate_interviews SET responses = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE candidate_id = ?",
            (json.dumps(responses), candidate_id)
        )

def update_candidate_interview_evaluation(candidate_id: int, score: float, summary: str, strengths: list, weaknesses: list, ai_review: str, recommendation: str):
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE candidate_interviews 
            SET score = ?, summary = ?, strengths = ?, weaknesses = ?, ai_review = ?, recommendation = ? 
            WHERE candidate_id = ?""",
            (score, summary, json.dumps(strengths), json.dumps(weaknesses), ai_review, recommendation, candidate_id)
        )
