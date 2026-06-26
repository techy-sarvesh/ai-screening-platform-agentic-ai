# AI Candidate Screening Platform

An AI-powered candidate screening platform designed to streamline recruitment workflows by automatically shortlisting, testing, and interviewing candidates using local large language models.

---

## Key Features

1. **Job Board Management**: Publish and view job openings, target experience requirements, and skill sets.
2. **AI Resume Screening**: Extract candidate profiles (skills, projects, education, work experience) from uploaded resumes (PDF, DOCX, TXT) and calculate a weighted match score:
   $$\text{Resume Score} = 40\% \text{ Skills} + 30\% \text{ Experience} + 20\% \text{ Projects} + 10\% \text{ Education}$$
3. **Comparative Leaderboard**: Sort, filter, and search candidates by match scores and recommendations.
4. **AI Technical Assessments**: Contextually generate MCQ, short-answer, and coding questions based on job description.
5. **FastAPI Candidate Test Site**: Unique test links where candidates submit code solutions and answers, evaluated automatically by the AI evaluator.
6. **AI Custom Interviews**: Dynamically generate personalized behavioral and technical questions targeting the candidate's exact screening weaknesses.
7. **FastAPI Candidate Interview Site**: Unique interactive interview page for writing responses to custom questions.
8. **Explainable AI Grading Reports**: Recruiter dashboard displays grading results, strengths/weaknesses breakdown, AI review comments, and final hiring recommendations (Strong Hire, Hire, Consider, Reject).

---

## Technical Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI & Jinja2 templates
- **Database**: SQLite
- **AI Integration**: Ollama (Qwen3:8B model) via LangChain (`langchain-ollama`)
- **Document Extractors**: `pypdf`, `python-docx`
- **Dependency Manager**: `uv`

---

## Folder Structure

```text
ai-screening-platform/
├── app.py                     # FastAPI Entrypoint (Candidate Portal)
├── main.py                    # Main Entrypoint script
├── pyproject.toml             # Dependencies config
├── README.md                  # Documentation
│
├── database/
│   ├── sqlite.db              # Database file (generated)
│   └── db.py                  # Database CRUD and helpers
│
├── models/
│   ├── job.py                 # Job Posting Pydantic model
│   ├── candidate.py           # Candidate profile Pydantic model
│   ├── screening_result.py    # Resume screening score model
│   └── assessment.py          # Assessment templates and instances
│
├── services/
│   ├── llm_service.py         # Ollama ChatOllama connection handler
│   ├── resume_service.py      # PDF/DOCX extractors
│   ├── scoring_service.py     # Math score logic helpers
│   └── assessment_service.py  # Link/token generators
│
├── agents/
│   ├── screening_agent.py     # Resume parser & screener
│   ├── ranking_agent.py       # Leaderboard and comparative reporter
│   ├── assessment_agent.py    # Test generator and evaluator
│   └── interview_agent.py     # Custom interview generator and evaluator
│
├── prompts/
│   ├── screening_prompt.py    # Resume extraction & screening prompts
│   ├── ranking_prompt.py      # Comparison ranking report prompt
│   ├── assessment_prompt.py   # Test generation & evaluation prompts
│   └── interview_prompt.py    # Custom interview generation & grading prompts
│
├── templates/
│   ├── test_page.html         # FastAPI Candidate Test form
│   ├── interview_page.html    # FastAPI Candidate Interview form
│   └── thank_you.html         # Submission confirmation page
│
├── uploads/
│   └── resumes/               # Location to save uploaded resumes
│
└── tests/
    └── test_platform.py       # Pytest unit tests
```

---

## Running the Platform

Ensure you have [Ollama](https://ollama.ai/) installed and running locally with the `qwen3:8b` model pulled:
```bash
ollama run qwen3:8b
```

### 1. Set Up Environment
Create virtual environment and install packages:
```bash
uv venv
source .venv/bin/activate
uv add streamlit fastapi uvicorn pydantic requests pypdf python-docx langchain langchain-ollama pytest
```

### 2. Start the Backend API (FastAPI)
Run the backend server on port 8000 (required to serve test/interview pages):
```bash
uvicorn app:app --port 8000 --reload
```

### 3. Start the Recruiter Portal (Streamlit)
Run the dashboard in a separate terminal:
```bash
streamlit run ui/dashboard.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Running Tests

Verify database, scoring calculations, and token utilities using pytest:
```bash
pytest tests/
```
