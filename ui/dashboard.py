import streamlit as st
import os
import sys
import shutil

# Add workspace directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import importlib
import database.db
importlib.reload(database.db)
from database import db

import services.resume_service
import services.assessment_service
importlib.reload(services.resume_service)
importlib.reload(services.assessment_service)
from services import resume_service, assessment_service

import agents.screening_agent
import agents.ranking_agent
import agents.assessment_agent
import agents.interview_agent
importlib.reload(agents.screening_agent)
importlib.reload(agents.ranking_agent)
importlib.reload(agents.assessment_agent)
importlib.reload(agents.interview_agent)
from agents import screening_agent, ranking_agent, assessment_agent, interview_agent

# Initialize database
db.init_db()

# Page configuration
st.set_page_config(
    page_title="AI Screening Platform",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling (Clean, simple, high-contrast dark theme)
st.markdown("""
<style>
    /* Main Layout */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Headers styling */
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        color: #ffffff;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main-title {
        font-size: 2.25rem;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    
    .subtitle {
        color: #9ca3af;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    
    /* Cards and Funnels */
    .card {
        background-color: #131b2e;
        border: 1px solid #222f4d;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 0.4rem;
    }
    
    .badge-strong-hire {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .badge-hire {
        background-color: rgba(99, 102, 241, 0.15);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    
    .badge-consider {
        background-color: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .badge-reject {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.markdown('<div class="main-title">AI Screening Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Simplified recruitment workflows with smart AI resume screening and candidate benchmark Funnels.</div>', unsafe_allow_html=True)

# --- SIDEBAR MODEL CONFIG & NAVIGATION ---
st.sidebar.markdown("### ⚙️ Navigation")
menu = st.sidebar.radio(
    "Select Workspace",
    [
        "🔄 Recruitment Funnel", 
        "💼 Job Openings", 
        "📥 Resumes Upload & Screening", 
        "📊 Candidate Leaderboards", 
        "📊 Cross-Job Dashboard", 
        "📝 Automated Assessments", 
        "🎤 AI Interviews"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Model Config")

# Active model switching logic
current_model = db.get_setting("active_model", "Qwen3:8B (Local)")
model_choices = ["Qwen3:8B (Local)", "ChatGPT 5.5 (Cloud)"]
model_index = model_choices.index(current_model) if current_model in model_choices else 0

selected_model = st.sidebar.selectbox("Choose AI Engine:", model_choices, index=model_index)

if selected_model != current_model:
    db.set_setting("active_model", selected_model)
    st.toast(f"Switched AI engine to: {selected_model}", icon="🤖")
    st.rerun()

# Info notice for ChatGPT 5.5 (Cloud) API key from env
if selected_model == "ChatGPT 5.5 (Cloud)":
    st.sidebar.info("🤖 **Note:** Ensure your `OPENAI_API_KEY` environment variable is set.")

# Configure upload path
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads", "resumes"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 1. RECRUITMENT PIPELINE FUNNEL (SIMPLIFIED WORKFLOW COCKPIT) ---
if menu == "🔄 Recruitment Funnel":
    st.header("Pipeline Funnel Cockpit")
    
    jobs = db.get_all_jobs()
    if not jobs:
        st.warning("Please create a Job Posting first under 'Job Openings'.")
    else:
        job_options = {f"{j['title']} (ID: {j['id']})": j['id'] for j in jobs}
        selected_job_label = st.selectbox("Select Target Job Opening", list(job_options.keys()))
        selected_job_id = job_options[selected_job_label]
        
        job = db.get_job(selected_job_id)
        candidates = ranking_agent.get_ranked_candidates(selected_job_id)
        assess_template = db.get_assessment_by_job(selected_job_id)
        
        # Calculate stats
        total_candidates = len(candidates)
        screened_count = len([c for c in candidates if c["overall_score"] > 0])
        assessment_sent = len([c for c in candidates if c["assessment_status"] != "None"])
        assessment_completed = len([c for c in candidates if c["assessment_status"] == "completed"])
        
        # Shortlisted candidates
        shortlisted = [
            c for c in candidates 
            if c["assessment_status"] == "completed" and c["final_score"] is not None and c["final_score"] >= 70.0
        ]
        
        col_funnel, col_short = st.columns([1.5, 1])
        
        with col_funnel:
            st.subheader(" funnel Pipeline Overview")
            
            # Step 1
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid #10b981;">
                <strong>Stage 1: Job Opening defined</strong> <span style="float:right; color:#10b981;">✅ COMPLETED</span>
                <div style="font-size:0.85rem; color:#9ca3af; margin-top:0.25rem;">
                    Active Title: <strong>{job['title']}</strong> | Req Experience: {job['experience_years']} Years
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Step 2 & 3
            screening_status = "✅ COMPLETED" if total_candidates > 0 else "🔵 IN PROGRESS"
            screening_border = "#10b981" if total_candidates > 0 else "#6366f1"
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid {screening_border};">
                <strong>Stage 2 & 3: Resume Ingestion & AI Screening</strong> <span style="float:right; color:{screening_border};">{screening_status}</span>
                <div style="font-size:0.85rem; color:#9ca3af; margin-top:0.25rem;">
                    Ingested: <strong>{total_candidates}</strong> | Screened: <strong>{screened_count}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Step 4
            ranking_status = "✅ COMPLETED" if screened_count > 0 else "⚪ PENDING"
            ranking_border = "#10b981" if screened_count > 0 else "#9ca3af"
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid {ranking_border};">
                <strong>Stage 4: Candidate Ranking</strong> <span style="float:right; color:{ranking_border};">{ranking_status}</span>
                <div style="font-size:0.85rem; color:#9ca3af; margin-top:0.25rem;">
                    Leaderboard generated. Top candidate profile: <strong>{candidates[0]['name'] if candidates else 'None'}</strong>.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Step 5
            assess_status = "✅ COMPLETED" if assess_template else "🔵 IN PROGRESS"
            assess_border = "#10b981" if assess_template else "#6366f1"
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid {assess_border};">
                <strong>Stage 5: Generate Assessment template</strong> <span style="float:right; color:{assess_border};">{assess_status}</span>
                <div style="font-size:0.85rem; color:#9ca3af; margin-top:0.25rem;">
                    {f"Technical test template ready: '{assess_template['title']}'." if assess_template else "No test template created yet."}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Step 6 & 7
            eval_status = "✅ COMPLETED" if assessment_completed > 0 else ("🔵 IN PROGRESS" if assessment_sent > 0 else "⚪ PENDING")
            eval_border = "#10b981" if assessment_completed > 0 else ("#6366f1" if assessment_sent > 0 else "#9ca3af")
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid {eval_border};">
                <strong>Stage 6 & 7: Candidate Testing & AI Evaluation</strong> <span style="float:right; color:{eval_border};">{eval_status}</span>
                <div style="font-size:0.85rem; color:#9ca3af; margin-top:0.25rem;">
                    Tests Sent: <strong>{assessment_sent}</strong> | Evaluated: <strong>{assessment_completed}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Step 8
            shortlist_status = "✅ COMPLETED" if len(shortlisted) > 0 else "🔵 IN PROGRESS"
            shortlist_border = "#10b981" if len(shortlisted) > 0 else "#6366f1"
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid {shortlist_border};">
                <strong>Stage 8: Final Shortlist recommendation</strong> <span style="float:right; color:{shortlist_border};">{shortlist_status}</span>
                <div style="font-size:0.85rem; color:#9ca3af; margin-top:0.25rem;">
                    Candidates ready for face-to-face round: <strong>{len(shortlisted)}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_short:
            st.subheader("⭐️ Qualified Candidates")
            if not shortlisted:
                st.info("No candidates have qualified for the final shortlist yet. (Requires test score >= 70%).")
            else:
                for c in shortlisted:
                    st.markdown(f"""
                    <div class="card" style="border-left: 5px solid #34d399;">
                        <h4 style="margin:0; font-size:1.1rem; color:#ffffff;">{c['name']}</h4>
                        <div style="font-size:0.8rem; color:#9ca3af; margin-top:0.2rem;">
                            Score: <strong style="color:#34d399;">{c['final_score']:.1f}%</strong> | Exp: {c['experience_years']} Yrs
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# --- 2. JOB OPENINGS PAGE (SIMPLIFIED CREATION) ---
elif menu == "💼 Job Openings":
    st.header("Job Position Settings")
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("Publish New Job Profile")
        
        # Simple upload to autofill
        autofill_file = st.file_uploader(
            "⚡ Drop a file to auto-fill details:",
            type=["pdf", "docx", "txt"],
            key="job_autofill_uploader"
        )
        
        if autofill_file:
            if st.button("AI Auto-fill Form"):
                with st.spinner("Parsing requirements..."):
                    temp_path = os.path.join(UPLOAD_DIR, f"temp_autofill_{autofill_file.name}")
                    with open(temp_path, "wb") as f:
                        shutil.copyfileobj(autofill_file, f)
                    
                    try:
                        doc_text = resume_service.extract_text_from_file(temp_path)
                        import importlib
                        import prompts.screening_prompt
                        importlib.reload(prompts.screening_prompt)
                        from prompts.screening_prompt import JOB_DESCRIPTION_EXTRACTION_PROMPT
                        from services import llm_service
                        
                        job_data = llm_service.generate_json(JOB_DESCRIPTION_EXTRACTION_PROMPT, {"document_text": doc_text})
                        
                        st.session_state["autofill_title"] = job_data.get("title", "")
                        st.session_state["autofill_desc"] = job_data.get("description", "")
                        st.session_state["autofill_skills"] = ", ".join(job_data.get("required_skills", []))
                        try:
                            st.session_state["autofill_exp"] = int(job_data.get("experience_years", 3))
                        except:
                            st.session_state["autofill_exp"] = 3
                            
                        st.success("Details extracted successfully! Form updated below.")
                    except Exception as e:
                        st.error(f"Failed to auto-fill details: {e}")
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            
        with st.form("create_job_form", clear_on_submit=True):
            title = st.text_input("Job Title", value=st.session_state.get("autofill_title", ""))
            description = st.text_area("Job Description", value=st.session_state.get("autofill_desc", ""))
            required_skills_input = st.text_input("Required Skills (comma-separated)", value=st.session_state.get("autofill_skills", ""))
            experience_years = st.number_input("Experience Required (Years)", min_value=0, value=st.session_state.get("autofill_exp", 3))
            assessment_required = st.checkbox("Assessment Required", value=True)
            
            submit_btn = st.form_submit_button("Publish Job Posting")
            
            if submit_btn:
                if not title or not description or not required_skills_input:
                    st.error("Please fill in the details.")
                else:
                    skills_list = [s.strip() for s in required_skills_input.split(",") if s.strip()]
                    db.create_job(title, description, skills_list, experience_years, assessment_required)
                    st.success(f"Job '{title}' published!")
                    for k in ["autofill_title", "autofill_desc", "autofill_skills", "autofill_exp"]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()
                    
    with col2:
        st.subheader("📋 Active Openings")
        jobs = db.get_all_jobs()
        if not jobs:
            st.info("No openings published.")
        else:
            for job in jobs:
                with st.expander(f"💼 {job['title']} (Req: {job['experience_years']} yrs)", expanded=False):
                    skills_html = "".join([f'<span class="badge badge-hire">{s}</span>' for s in job['required_skills']])
                    st.markdown(skills_html, unsafe_allow_html=True)
                    st.info(job['description'])

# --- 3. RESUMES UPLOAD & AI SCREENING ---
elif menu == "📥 Resumes Upload & Screening":
    st.header("Resume Upload & Ingestion")
    
    jobs = db.get_all_jobs()
    if not jobs:
        st.warning("Please publish a Job Opening first.")
    else:
        job_options = {f"{j['title']} (ID: {j['id']})": j['id'] for j in jobs}
        selected_job_label = st.selectbox("Select Job Position", list(job_options.keys()))
        selected_job_id = job_options[selected_job_label]
        
        tab_up, tab_sc = st.tabs(["📤 Upload Resumes", "🔎 Screening Fit"])
        
        with tab_up:
            uploaded_files = st.file_uploader("Upload resumes (PDF/DOCX/TXT) in bulk:", accept_multiple_files=True)
            if uploaded_files:
                if st.button("Ingest & Screen Candidate Profiles"):
                    progress_text = "Parsing candidates..."
                    my_bar = st.progress(0, text=progress_text)
                    total = len(uploaded_files)
                    
                    for idx, file in enumerate(uploaded_files):
                        file_path = os.path.join(UPLOAD_DIR, file.name)
                        with open(file_path, "wb") as f:
                            shutil.copyfileobj(file, f)
                        try:
                            text = resume_service.extract_text_from_file(file_path)
                            screening_agent.screen_candidate(text, selected_job_id, file.name, file_path)
                            st.toast(f"Ingested {file.name}", icon="✅")
                        except Exception as e:
                            st.error(f"Error {file.name}: {e}")
                        my_bar.progress((idx + 1) / total, text=f"Processed {idx + 1}/{total} candidates")
                    st.success("Screening Complete!")
                    
        with tab_sc:
            candidates = ranking_agent.get_ranked_candidates(selected_job_id)
            if not candidates:
                st.info("No candidates screened yet.")
            else:
                for c in candidates:
                    badge_class = "badge-consider"
                    if c["recommendation"] in ["Strong Hire", "Proceed to Assessment"]:
                        badge_class = "badge-strong-hire"
                    elif c["recommendation"] == "Reject":
                        badge_class = "badge-reject"
                        
                    st.markdown(f"""
                    <div class="card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0;">👤 {c['name']} (Exp: {c['experience_years']} Yrs)</h4>
                            <div>
                                <span class="badge {badge_class}">{c['recommendation']}</span>
                                <span style="font-size:1.15rem; font-weight:700; color:#818cf8;">{c['overall_score']:.1f}</span>
                            </div>
                        </div>
                        <div style="font-size:0.85rem; color:#9ca3af; margin-top:0.4rem;">{c['summary']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander(f"👁️ Show Fit breakdown for {c['name']}"):
                        sc1, sc2 = st.columns(2)
                        with sc1:
                            st.write(f"**Skills Fit:** {c['skills_score']:.1f}%")
                            st.write(f"**Experience Fit:** {c['experience_score']:.1f}%")
                            st.write(f"**Projects Match:** {c['projects_score']:.1f}%")
                        with sc2:
                            st.write("**AI Analysis Summary:**")
                            st.info(db.get_screening_result(c["id"])["summary"])
                        
                        st.write("**Strengths:**")
                        for s in db.get_screening_result(c["id"])["strengths"]:
                            st.success(s)

# --- 4. CANDIDATE LEADERBOARD ---
elif menu == "📊 Candidate Leaderboards":
    st.header("Job Leadboards")
    
    jobs = db.get_all_jobs()
    if not jobs:
        st.warning("Please publish a Job Opening first.")
    else:
        job_options = {f"{j['title']} (ID: {j['id']})": j['id'] for j in jobs}
        selected_job_label = st.selectbox("Select Open Position Profile", list(job_options.keys()))
        selected_job_id = job_options[selected_job_label]
        
        candidates = ranking_agent.get_ranked_candidates(selected_job_id)
        if not candidates:
            st.info("No candidates registered.")
        else:
            col1, col2 = st.columns([1, 1.2])
            with col1:
                for rank, c in enumerate(candidates, 1):
                    badge_color = "#34d399" if c["recommendation"] == "Proceed to Assessment" else "#9ca3af"
                    if c["recommendation"] == "Reject":
                        badge_color = "#f87171"
                    st.markdown(f"""
                    <div class="card" style="border-left: 4px solid {badge_color};">
                        <div style="display:flex; justify-content:space-between;">
                            <span><strong>#{rank}</strong> {c['name']}</span>
                            <span style="color:#a855f7; font-weight:700;">{c['overall_score']:.1f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            with col2:
                if st.button("Generate comparative report"):
                    with st.spinner("AI is analyzing leaderboard..."):
                        report = ranking_agent.generate_ranking_report(selected_job_id)
                        st.session_state[f"leader_rep_{selected_job_id}"] = report
                
                rep_key = f"leader_rep_{selected_job_id}"
                if rep_key in st.session_state:
                    st.markdown(st.session_state[rep_key])
                else:
                    st.info("Click the button above to generate comparative analysis report.")

# --- 5. CROSS-JOB DASHBOARD ---
elif menu == "📊 Cross-Job Dashboard":
    st.header("Global Talent benchmarking")
    
    candidates = ranking_agent.get_cross_job_ranked_candidates()
    if not candidates:
        st.info("No screened profiles found.")
    else:
        # Simplified filters
        search_query = st.text_input("🔍 Search globally by Name, Email, or Skills tags:", value="")
        
        filtered = []
        for c in candidates:
            if (search_query.lower() in c["name"].lower() or 
                search_query.lower() in c["email"].lower() or 
                any(search_query.lower() in s.lower() for s in c["skills"])):
                filtered.append(c)
                
        if not filtered:
            st.info("No candidate profiles match search criteria.")
        else:
            col_list, col_ai = st.columns([1.2, 1])
            with col_list:
                compare_opts = {f"{c['name']} (Applied: {c['job_title']} - Score: {c['overall_score']:.1f})": c["id"] for c in filtered}
                selected_compare = st.multiselect("Benchmarking Selection (Max 4):", list(compare_opts.keys()), max_selections=4)
                
                for c in filtered:
                    st.markdown(f"""
                    <div class="card">
                        <strong>{c['name']}</strong> ({c['job_title']})
                        <div style="font-size:0.8rem; color:#9ca3af; margin-top:0.25rem;">
                            Resume Score: {c['overall_score']:.1f} | Test Score: {c['assessment_score'] or 'N/A'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            with col_ai:
                if not selected_compare:
                    st.info("Select profiles to cross-compare and benchmark candidate fitments.")
                else:
                    cids = [compare_opts[lbl] for lbl in selected_compare]
                    if st.button("Generate Principal Fit Analysis"):
                        with st.spinner("Generating comparative analysis..."):
                            rep = ranking_agent.generate_cross_job_comparison_report(cids)
                            st.session_state["cross_rep"] = rep
                            
                    if "cross_rep" in st.session_state:
                        st.markdown(st.session_state["cross_rep"])

# --- 6. AUTOMATED ASSESSMENTS ---
elif menu == "📝 Automated Assessments":
    st.header("Technical test administration")
    
    jobs = db.get_all_jobs()
    if not jobs:
        st.warning("Please publish a Job Opening first.")
    else:
        job_options = {f"{j['title']} (ID: {j['id']})": j['id'] for j in jobs}
        selected_job_label = st.selectbox("Select Target Opening Profile", list(job_options.keys()))
        selected_job_id = job_options[selected_job_label]
        
        assess_template = db.get_assessment_by_job(selected_job_id)
        col_test, col_cand = st.columns([1, 1.2])
        
        with col_test:
            st.subheader("Test Questions Setup")
            if not assess_template:
                if st.button("Generate Assessment Template via AI"):
                    with st.spinner("AI is generating questions..."):
                        assessment_agent.generate_and_save_assessment(selected_job_id)
                        st.success("Test template generated successfully!")
                        st.rerun()
            else:
                st.success(f"✅ Technical test template ready.")
                with st.expander("👁️ View Generated Questions"):
                    for idx, q in enumerate(assess_template["questions"], 1):
                        st.write(f"**Q{idx}. [{q['section']}]** {q['question']}")
                        
        with col_cand:
            st.subheader("Candidate Links & Results")
            candidates = ranking_agent.get_ranked_candidates(selected_job_id)
            proceed_cands = [c for c in candidates if c["recommendation"] == "Proceed to Assessment" or c["assessment_status"] != "None"]
            
            if not proceed_cands:
                st.info("No candidates ready for assessment.")
            else:
                cand_map = {c["name"]: c for c in proceed_cands}
                sel_cand_name = st.selectbox("Choose Candidate", list(cand_map.keys()))
                sel_cand = cand_map[sel_cand_name]
                
                cand_assess = db.get_candidate_assessment(sel_cand["id"])
                if not cand_assess:
                    if st.button(f"Generate Assessment URL for {sel_cand['name']}"):
                        token = assessment_service.generate_assessment_token()
                        db.create_candidate_assessment(sel_cand["id"], assess_template["id"], token)
                        st.success("Test link ready!")
                        st.rerun()
                else:
                    test_url = assessment_service.generate_assessment_url("http://localhost:8000", cand_assess["token"])
                    st.write(f"**Status:** `{cand_assess['status'].upper()}`")
                    st.code(test_url)
                    
                    if cand_assess["status"] == "completed":
                        st.markdown(f"""
                        <div class="card" style="margin-top:1rem;">
                            <strong>Technical Score:</strong> {cand_assess['technical_score']:.1f}/10 <br>
                            <strong>Final combined score:</strong> <span style="color:#a855f7; font-weight:700;">{cand_assess['final_score']:.1f}%</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.write("**AI Review:**")
                        st.info(cand_assess["ai_review"])

# --- 7. AI INTERVIEWS ---
elif menu == "🎤 AI Interviews":
    st.header("Tailored Gaps Interviews")
    
    jobs = db.get_all_jobs()
    if not jobs:
        st.warning("Please publish a Job Opening first.")
    else:
        job_options = {f"{j['title']} (ID: {j['id']})": j['id'] for j in jobs}
        selected_job_label = st.selectbox("Select Target Opening Position", list(job_options.keys()))
        selected_job_id = job_options[selected_job_label]
        
        candidates = ranking_agent.get_ranked_candidates(selected_job_id)
        if not candidates:
            st.info("No candidate profiles available.")
        else:
            col_manage, col_res = st.columns([1, 1.2])
            with col_manage:
                cand_map = {c["name"]: c for c in candidates}
                sel_cand_name = st.selectbox("Select Target Candidate", list(cand_map.keys()))
                sel_cand = cand_map[sel_cand_name]
                
                interview = db.get_candidate_interview(sel_cand["id"])
                if not interview:
                    if st.button("Generate customized interview questions"):
                        with st.spinner("AI is targetting screening gaps..."):
                            interview_agent.generate_candidate_interview(sel_cand["id"])
                            st.success("Questions generated!")
                            st.rerun()
                else:
                    int_url = f"http://localhost:8000/interview/{interview['token']}"
                    st.code(int_url)
                    with st.expander("👁️ View custom questions"):
                        for i, q in enumerate(interview["questions"], 1):
                            st.write(f"**Q{i}. [{q['topic']}]** {q['question']}")
                    
                    st.markdown("---")
                    if interview["status"] == "completed":
                        st.warning("⚠️ Candidate has already submitted responses. Regenerating will reset responses and grades.")
                    if st.button("🔄 Regenerate custom interview", key=f"regen_{sel_cand['id']}"):
                        with st.spinner("AI is regenerating interview questions targeting gaps..."):
                            interview_agent.generate_candidate_interview(sel_cand["id"], force_regenerate=True)
                            st.success("Questions regenerated successfully!")
                            st.rerun()
            with col_res:
                if not interview or interview["status"] == "pending":
                    st.info("Waiting for candidate submission.")
                else:
                    st.markdown(f"""
                    <div class="card">
                        <strong>AI Interview Grade:</strong> {interview['score']:.1f}% <br>
                        <strong>AI Recommendation:</strong> {interview['recommendation']}
                    </div>
                    """, unsafe_allow_html=True)
                    st.info(interview["ai_review"])
