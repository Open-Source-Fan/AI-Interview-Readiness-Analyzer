"""
app.py — AI Interview Coach
Phase 1: CSS foundation + landing page + navigation
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from src.schemas import QAPair, ReadinessReport
from src.jd_parser import JDParser
from src.question_gen import QuestionGenerator
from src.evaluator import EvaluationEngine
from src.report_gen import generate_pdf

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS Foundation ────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1100px;
}
h1, h2, h3, h4 { font-family: 'Inter', sans-serif; color: #0f172a; }
p, li, span, div { color: #334155; }

/* ── Colour tokens ── */
:root {
    --primary:   #6366f1;
    --primary-d: #4f46e5;
    --success:   #10b981;
    --warning:   #f59e0b;
    --danger:    #ef4444;
    --surface:   #ffffff;
    --bg:        #f8fafc;
    --border:    #e2e8f0;
    --text-main: #0f172a;
    --text-muted:#64748b;
}

/* ── Card component ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.card-accent {
    border-left: 4px solid var(--primary);
}
.card-success {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 10px;
    padding: 1rem 1.25rem;
}
.card-warning {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 10px;
    padding: 1rem 1.25rem;
}
.card-danger {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 10px;
    padding: 1rem 1.25rem;
}

/* ── Hero section ── */
.hero {
    text-align: center;
    padding: 3.5rem 2rem 2.5rem;
    background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%);
    border-radius: 16px;
    margin-bottom: 2rem;
    border: 1px solid #e0e7ff;
}
.hero-badge {
    display: inline-block;
    background: #ede9fe;
    color: #5b21b6;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    padding: 0.3rem 0.85rem;
    border-radius: 999px;
    margin-bottom: 1.25rem;
    text-transform: uppercase;
}
.hero h1 {
    font-size: 2.8rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.2;
    margin-bottom: 0.75rem;
}
.hero p {
    font-size: 1.1rem;
    color: #64748b;
    max-width: 580px;
    margin: 0 auto 1.75rem;
    line-height: 1.7;
}

/* ── Feature cards ── */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 2rem 0;
}
.feature-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
}
.feature-icon {
    font-size: 1.75rem;
    margin-bottom: 0.5rem;
}
.feature-card h4 {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.3rem;
}
.feature-card p {
    font-size: 0.8rem;
    color: #64748b;
    line-height: 1.5;
}

/* ── Progress stepper ── */
.stepper {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin-bottom: 2rem;
    padding: 1rem;
    background: white;
    border-radius: 12px;
    border: 1px solid var(--border);
}
.step-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.step-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
}
.step-dot-active {
    background: var(--primary);
    color: white;
}
.step-dot-done {
    background: var(--success);
    color: white;
}
.step-dot-pending {
    background: #f1f5f9;
    color: #94a3b8;
    border: 2px solid var(--border);
}
.step-label {
    font-size: 0.82rem;
    font-weight: 500;
}
.step-label-active { color: var(--primary); }
.step-label-done   { color: var(--success); }
.step-label-pending{ color: #94a3b8; }
.step-connector {
    width: 48px;
    height: 2px;
    background: var(--border);
    margin: 0 0.25rem;
}
.step-connector-done { background: var(--success); }

/* ── Skill tag ── */
.tag {
    display: inline-block;
    background: #eff6ff;
    color: #1d4ed8;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    margin: 0.15rem;
    border: 1px solid #bfdbfe;
}
.tag-green {
    background: #f0fdf4;
    color: #16a34a;
    border-color: #bbf7d0;
}
.tag-red {
    background: #fef2f2;
    color: #dc2626;
    border-color: #fecaca;
}

/* ── Score hero card ── */
.score-hero {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    text-align: center;
    color: white;
    margin-bottom: 1.5rem;
}
.score-hero .score-number {
    font-size: 5rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.25rem;
}
.score-tier-badge {
    display: inline-block;
    padding: 0.35rem 1rem;
    border-radius: 999px;
    font-size: 0.9rem;
    font-weight: 600;
    margin: 0.5rem 0;
}
.tier-excellent { background: #10b981; color: white; }
.tier-good      { background: #f59e0b; color: white; }
.tier-needs     { background: #ef4444; color: white; }

/* ── Question card ── */
.question-card {
    background: white;
    border: 1px solid var(--border);
    border-left: 5px solid var(--primary);
    border-radius: 12px;
    padding: 1.75rem;
    margin: 1rem 0;
}
.question-card .q-type-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.badge-behavioural { background: #eff6ff; color: #1d4ed8; }
.badge-technical   { background: #fef2f2; color: #dc2626; }
.badge-situational { background: #fefce8; color: #a16207; }
.badge-culture_fit { background: #f0fdf4; color: #15803d; }
.question-card .q-text {
    font-size: 1.15rem;
    font-weight: 600;
    color: #0f172a;
    line-height: 1.5;
}

/* ── Progress dots ── */
.progress-dots {
    display: flex;
    gap: 0.4rem;
    margin-bottom: 1rem;
}
.dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
}
.dot-done    { background: var(--success); }
.dot-current { background: var(--primary); }
.dot-pending { background: #e2e8f0; }

/* ── Metric card ── */
.metric-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}
.metric-card .metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1;
}
.metric-card .metric-label {
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 0.25rem;
}
.metric-card .metric-bar {
    height: 4px;
    border-radius: 2px;
    margin-top: 0.5rem;
    background: #f1f5f9;
    overflow: hidden;
}
.metric-card .metric-fill {
    height: 100%;
    border-radius: 2px;
}

/* ── Section header ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--border);
}
.section-header .icon { font-size: 1.2rem; }
.section-header h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    margin: 0;
}

/* ── Feedback item ── */
.feedback-item {
    background: #f8fafc;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    border-left: 3px solid var(--primary);
    font-size: 0.875rem;
    color: #334155;
    line-height: 1.6;
}
.feedback-item strong { color: #1e293b; }

/* ── Improvement tip ── */
.tip-item {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    color: #78350f;
    line-height: 1.6;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
[data-testid="stSidebarNav"] { display: none; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    padding: 0.6rem 1.5rem !important;
}
.stButton > button[kind="secondary"] {
    background: white !important;
    color: #4f46e5 !important;
    border: 1.5px solid #6366f1 !important;
}

/* ── Text area ── */
.stTextArea textarea {
    border-radius: 10px !important;
    border: 1.5px solid var(--border) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    line-height: 1.6 !important;
}
.stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}

/* ── Metrics ── */
[data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { font-size: 0.8rem !important; color: #64748b !important; }

/* ── Sidebar (kept collapsed) ── */
[data-testid="stSidebar"] { display: none; }

/* ── Download button ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.6rem 1.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────

SAMPLE_JD = """We are hiring a Senior Backend Engineer to join our platform team.

Requirements:
- 4+ years of Python experience
- Strong knowledge of FastAPI, PostgreSQL, and REST API design
- Experience with Docker, Kubernetes, and cloud deployment (AWS/GCP)
- Familiarity with Redis, message queues (Kafka or RabbitMQ)
- Experience designing and scaling distributed systems

Responsibilities:
- Design and implement microservices for our data platform
- Optimize database queries and improve system performance
- Lead technical discussions and mentor junior engineers
- Drive architectural decisions and system design reviews"""

# ── Cached loaders ────────────────────────────────────────────────────────────

@st.cache_resource
def get_jd_parser():
    return JDParser()

@st.cache_resource
def get_question_generator():
    return QuestionGenerator()

@st.cache_resource
def get_evaluation_engine():
    return EvaluationEngine()

# ── Session state ─────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "step": 0,              # 0 = landing, 1 = setup, 2 = interview, 3 = report
        "parsed_jd": None,
        "question_bank": None,
        "current_q_idx": 0,
        "answers": {},
        "qa_pairs": [],
        "report": None,
        "jd_text": "",
        "interview_mode": "Mixed",
        "n_questions": 3,
        "demo_mode": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── Progress stepper ──────────────────────────────────────────────────────────

def render_stepper():
    """Horizontal progress stepper shown on steps 1-3."""
    step = st.session_state.step
    steps = ["Job Setup", "Mock Interview", "Report"]
    dots, labels, connectors = [], [], []

    for i, label in enumerate(steps, 1):
        if i < step:
            dot_cls   = "step-dot step-dot-done"
            lbl_cls   = "step-label step-label-done"
            dot_inner = "✓"
        elif i == step:
            dot_cls   = "step-dot step-dot-active"
            lbl_cls   = "step-label step-label-active"
            dot_inner = str(i)
        else:
            dot_cls   = "step-dot step-dot-pending"
            lbl_cls   = "step-label step-label-pending"
            dot_inner = str(i)

        dots.append(f'<div class="step-item"><div class="{dot_cls}">{dot_inner}</div><span class="{lbl_cls}">{label}</span></div>')
        if i < len(steps):
            conn_cls = "step-connector step-connector-done" if i < step else "step-connector"
            dots.append(f'<div class="{conn_cls}"></div>')

    html = f'<div class="stepper">{"".join(dots)}</div>'
    st.markdown(html, unsafe_allow_html=True)

# ── Top nav bar ───────────────────────────────────────────────────────────────

def render_topnav():
    """Minimal top navigation with logo and restart button."""
    col_logo, col_spacer, col_btn = st.columns([3, 6, 2])
    with col_logo:
        st.markdown(
            '<p style="font-size:1.1rem;font-weight:700;color:#4f46e5;margin:0;padding-top:0.3rem;">🎯 AI Interview Coach</p>',
            unsafe_allow_html=True
        )
    with col_btn:
        if st.session_state.step > 0:
            if st.button("↩ Start Over", key="topnav_restart"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
    st.markdown('<hr style="margin:0.5rem 0 1.5rem;border:none;border-top:1px solid #e2e8f0;">', unsafe_allow_html=True)

# ── Screen 0: Landing page ────────────────────────────────────────────────────

def render_landing():
    render_topnav()

    # Hero
    st.markdown("""
    <div class="hero">
        <div class="hero-badge">✨ AI-Powered Interview Preparation</div>
        <h1>Practice smarter.<br>Land the offer.</h1>
        <p>Generate role-specific interview questions from any job description, answer them in a guided session, and receive a detailed AI evaluation with explainable scores across 10 dimensions.</p>
    </div>
    """, unsafe_allow_html=True)

    # CTA buttons
    col1, col2, col3 = st.columns([2, 1.5, 2])
    with col2:
        if st.button("🚀 Start Session", type="primary", use_container_width=True, key="landing_start"):
            st.session_state.step = 1
            st.session_state.demo_mode = False
            st.rerun()

    col4, col5, col6 = st.columns([2.5, 1.5, 2.5])
    with col5:
        st.markdown('<p style="text-align:center;color:#94a3b8;font-size:0.8rem;margin:0.25rem 0;">or</p>', unsafe_allow_html=True)

    col7, col8, col9 = st.columns([2, 1.5, 2])
    with col8:
        if st.button("⚡ Try Demo", use_container_width=True, key="landing_demo"):
            st.session_state.step = 1
            st.session_state.demo_mode = True
            st.session_state.jd_text = SAMPLE_JD
            st.rerun()

    # Feature cards
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <h4>AI Interviewer</h4>
            <p>Gemini evaluates technical depth, reasoning quality, and answer maturity like a senior engineer would</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h4>Rule-Based Scoring</h4>
            <p>Deterministic signals check ownership language, quantified impact, and JD skill coverage objectively</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🗣️</div>
            <h4>Communication Analysis</h4>
            <p>spaCy measures reading clarity, filler words, passive voice, and vocabulary diversity</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <h4>PDF Report</h4>
            <p>Download a full readiness report with scores, AI feedback, and actionable improvement tips</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # How it works
    st.markdown("---")
    st.markdown('<p style="text-align:center;font-weight:600;font-size:1rem;color:#1e293b;margin-bottom:1.25rem;">How it works</p>', unsafe_allow_html=True)
    h1, h2, h3, h4 = st.columns(4)
    for col, num, title, desc in [
        (h1, "1", "Paste JD", "Paste any job description — we extract role, skills, and tech stack automatically"),
        (h2, "2", "Set Mode", "Choose Technical, Behavioural, or Mixed interview type and question count"),
        (h3, "3", "Answer", "Answer role-specific questions one at a time in a guided interview flow"),
        (h4, "4", "Get Report", "Receive a 4-section hybrid evaluation with a downloadable PDF"),
    ]:
        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:1rem;">
                <div style="width:36px;height:36px;border-radius:50%;background:#ede9fe;color:#5b21b6;
                            font-weight:700;font-size:1rem;display:flex;align-items:center;
                            justify-content:center;margin:0 auto 0.75rem;">{num}</div>
                <p style="font-weight:600;font-size:0.9rem;color:#1e293b;margin-bottom:0.25rem;">{title}</p>
                <p style="font-size:0.78rem;color:#64748b;line-height:1.5;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

# ── Screen 1: Job Setup ───────────────────────────────────────────────────────

def render_step1():
    render_topnav()
    render_stepper()

    st.markdown('<h2 style="margin-bottom:0.25rem;">Set Up Your Interview</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;margin-bottom:1.5rem;">Paste a job description and we\'ll generate tailored questions for your practice session.</p>', unsafe_allow_html=True)

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown('<div class="card card-accent">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:600;font-size:0.9rem;margin-bottom:0.5rem;">📋 Job Description</p>', unsafe_allow_html=True)

        col_sample, col_clear = st.columns([2, 1])
        with col_sample:
            if st.button("Use sample JD", key="sample_btn"):
                st.session_state.jd_text = SAMPLE_JD
                st.session_state.jd_textarea = SAMPLE_JD
        with col_clear:
            if st.button("Clear", key="clear_btn"):
                st.session_state.jd_text = ""
                st.session_state.jd_textarea = ""

        jd_text = st.text_area(
            "Paste job description here",
            value=st.session_state.jd_text,
            height=280,
            placeholder="Paste a real job description here — the more detail, the better your questions...",
            key="jd_textarea",
            label_visibility="collapsed",
        )
        st.session_state.jd_text = jd_text
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        # Interview mode selector
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:600;font-size:0.9rem;margin-bottom:0.75rem;">🎯 Interview Mode</p>', unsafe_allow_html=True)

        mode = st.radio(
            "Select interview type",
            ["Mixed", "Behavioural Only", "Technical Only"],
            index=["Mixed", "Behavioural Only", "Technical Only"].index(
                st.session_state.get("interview_mode", "Mixed")
            ),
            key="mode_radio",
            label_visibility="collapsed",
        )
        st.session_state.interview_mode = mode

        mode_desc = {
            "Mixed":             "All question types: behavioural, technical, situational, and culture fit",
            "Behavioural Only":  "Focus on past experience and STAR-format answers",
            "Technical Only":    "System design, coding approach, and technical problem-solving",
        }
        st.markdown(f'<p style="font-size:0.78rem;color:#64748b;margin-top:0.25rem;">{mode_desc[mode]}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Question count
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p style="font-weight:600;font-size:0.9rem;margin-bottom:0.5rem;">❓ Questions</p>', unsafe_allow_html=True)
        n_questions = st.slider(
            "Number of questions",
            min_value=1, max_value=10, value=st.session_state.n_questions,
            label_visibility="collapsed",
            key="q_slider",
        )
        st.session_state.n_questions = n_questions
        st.markdown(f'<p style="font-size:0.78rem;color:#64748b;">Estimated time: {n_questions * 3}–{n_questions * 5} minutes</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Demo mode indicator
        if st.session_state.demo_mode:
            st.markdown("""
            <div style="background:#ede9fe;border:1px solid #c4b5fd;border-radius:10px;padding:0.75rem 1rem;margin-bottom:1rem;">
                <p style="font-size:0.8rem;font-weight:600;color:#5b21b6;margin:0;">⚡ Demo Mode Active</p>
                <p style="font-size:0.75rem;color:#6d28d9;margin:0.25rem 0 0;">Sample Backend Engineer JD is pre-loaded</p>
            </div>
            """, unsafe_allow_html=True)

    # Generate button
    st.markdown("<br>", unsafe_allow_html=True)
    btn_col1, btn_col2, btn_col3 = st.columns([3, 2, 3])
    with btn_col2:
        generate = st.button("Generate Questions →", type="primary", use_container_width=True, key="gen_btn")

    if generate:
        text = st.session_state.jd_text.strip()
        if len(text) < 20:
            st.error("Please paste a job description (at least 20 characters).")
            return

        with st.spinner("Parsing job description..."):
            parser = get_jd_parser()
            parsed_jd = parser.parse(text)
            st.session_state.parsed_jd = parsed_jd

        # Filter questions by mode
        with st.spinner("Generating questions with Gemini..."):
            gen = get_question_generator()
            bank = gen.generate(parsed_jd)

            mode = st.session_state.interview_mode
            if mode == "Behavioural Only":
                filtered = [q for q in bank.questions if q.type.value in ("behavioural", "situational")]
            elif mode == "Technical Only":
                filtered = [q for q in bank.questions if q.type.value == "technical"]
            else:
                filtered = bank.questions

            if not filtered:
                filtered = bank.questions  # fallback if filter empties list

            bank.questions = filtered[:n_questions]
            st.session_state.question_bank = bank

        st.session_state.step = 2
        st.session_state.current_q_idx = 0
        st.session_state.answers = {}
        st.session_state.report = None
        st.rerun()

# ── Screen 2: Mock Interview ──────────────────────────────────────────────────

def render_step2():
    render_topnav()
    render_stepper()

    bank  = st.session_state.question_bank
    total = len(bank.questions)
    idx   = st.session_state.current_q_idx

    if idx >= total:
        qa_pairs = []
        for i, q in enumerate(bank.questions):
            ans = st.session_state.answers.get(i, "").strip()
            if ans:
                qa_pairs.append(QAPair(question=q, answer=ans))
        st.session_state.qa_pairs = qa_pairs
        st.session_state.step = 3
        st.rerun()
        return

    q = bank.questions[idx]

    # Progress bar row
    prog_left, prog_right = st.columns([5, 2])
    with prog_left:
        # Progress dots
        dots_html = '<div class="progress-dots">'
        for i in range(total):
            if i < idx:
                dots_html += '<div class="dot dot-done"></div>'
            elif i == idx:
                dots_html += '<div class="dot dot-current"></div>'
            else:
                dots_html += '<div class="dot dot-pending"></div>'
        dots_html += '</div>'
        st.markdown(dots_html, unsafe_allow_html=True)
    with prog_right:
        st.markdown(
            f'<p style="text-align:right;font-size:0.85rem;color:#64748b;font-weight:500;">Question {idx+1} of {total}</p>',
            unsafe_allow_html=True
        )

    st.progress((idx) / total)

    # Question card
    badge_cls = {
        "behavioural":  "badge-behavioural",
        "technical":    "badge-technical",
        "situational":  "badge-situational",
        "culture_fit":  "badge-culture_fit",
    }.get(q.type.value, "badge-behavioural")

    badge_label = q.type.value.replace("_", " ").title()

    st.markdown(f"""
    <div class="question-card">
        <span class="q-type-badge {badge_cls}">{badge_label}</span>
        &nbsp;
        <span style="font-size:0.72rem;color:#94a3b8;font-weight:500;">Difficulty: {q.difficulty}</span>
        <div class="q-text">{q.text}</div>
    </div>
    """, unsafe_allow_html=True)

    # STAR tip (inline, not hidden)
    if q.star_applicable:
        st.markdown("""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.75rem;">
            <p style="font-size:0.78rem;font-weight:600;color:#64748b;margin:0 0 0.3rem;">💡 STAR Framework</p>
            <p style="font-size:0.78rem;color:#64748b;margin:0;line-height:1.6;">
                <strong>S</strong>ituation — set the context &nbsp;·&nbsp;
                <strong>T</strong>ask — your goal &nbsp;·&nbsp;
                <strong>A</strong>ction — what YOU did &nbsp;·&nbsp;
                <strong>R</strong>esult — measurable outcome
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Answer area
    answer = st.text_area(
        "Your answer",
        value=st.session_state.answers.get(idx, ""),
        height=200,
        placeholder="Structure your answer clearly. Use 'I' not 'we'. Include specific actions and measurable results...",
        key=f"answer_q{idx}",
        label_visibility="collapsed",
    )
    st.session_state.answers[idx] = answer

    # Word count
    word_count = len(answer.split()) if answer.strip() else 0
    wc_colour = "#10b981" if 80 <= word_count <= 200 else "#f59e0b" if word_count > 0 else "#94a3b8"
    st.markdown(
        f'<p style="font-size:0.75rem;color:{wc_colour};text-align:right;margin-top:-0.5rem;">{word_count} words · aim for 80–200</p>',
        unsafe_allow_html=True
    )

    # Navigation
    nav_l, nav_mid, nav_r = st.columns([1, 5, 1])
    with nav_l:
        if idx > 0:
            if st.button("← Back", key=f"back_{idx}"):
                st.session_state.current_q_idx -= 1
                st.rerun()
    with nav_r:
        label = "Finish ✓" if idx == total - 1 else "Next →"
        if st.button(label, type="primary", key=f"next_{idx}"):
            if not answer.strip():
                st.warning("Please type an answer before continuing.")
            else:
                st.session_state.current_q_idx += 1
                st.rerun()

# ── Screen 3: Report Dashboard ────────────────────────────────────────────────

def _tier_info(score: float) -> tuple:
    """Returns (label, badge_class, colour_hex)"""
    if score >= 75:
        return "Excellent", "tier-excellent", "#10b981"
    if score >= 50:
        return "Good", "tier-good", "#f59e0b"
    return "Needs Work", "tier-needs", "#ef4444"

def _bar(value: float, max_val: float = 10.0, colour: str = "#6366f1") -> str:
    pct = min(value / max_val * 100, 100)
    return f"""
    <div class="metric-bar">
        <div class="metric-fill" style="width:{pct:.0f}%;background:{colour};"></div>
    </div>"""

def render_step3():
    render_topnav()
    render_stepper()

    # ── Evaluate if needed ─────────────────────────────────────────────────
    if st.session_state.report is None:
        qa_pairs  = st.session_state.qa_pairs
        parsed_jd = st.session_state.parsed_jd

        if not qa_pairs:
            st.error("No answers found. Please complete the mock interview first.")
            if st.button("← Back to Interview"):
                st.session_state.step = 2
                st.session_state.current_q_idx = 0
                st.rerun()
            return

        with st.status("🤖 Running hybrid evaluation...", expanded=True) as status:
            st.write("**Step 1/3** — AI Interviewer Assessment (Gemini)...")
            st.write("**Step 2/3** — Rule-based scoring (ownership, impact, skill coverage)...")
            st.write("**Step 3/3** — Communication analysis (spaCy + textstat)...")
            engine      = get_evaluation_engine()
            evaluations = engine.evaluate_all(qa_pairs, parsed_jd=parsed_jd)
            report      = ReadinessReport.from_evaluations(evaluations, parsed_jd)
            st.session_state.report = report
            status.update(label="✅ Evaluation complete!", state="complete")

    report: ReadinessReport = st.session_state.report
    tier_label, tier_cls, tier_hex = _tier_info(report.overall_score)

    # ── Hero score card ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="score-hero">
        <p style="color:#94a3b8;font-size:0.85rem;font-weight:500;margin-bottom:0.5rem;">
            {report.role} &nbsp;·&nbsp; {len(report.evaluations)} question{"s" if len(report.evaluations) != 1 else ""} evaluated
        </p>
        <div class="score-number" style="color:{tier_hex};">{report.overall_score:.0f}</div>
        <p style="color:#94a3b8;font-size:0.9rem;margin:0;">out of 100</p>
        <span class="score-tier-badge {tier_cls}">{tier_label}</span>
        <p style="color:#94a3b8;font-size:0.78rem;margin-top:0.75rem;">
            Hybrid score: 40% AI Interviewer · 35% Rule-Based · 25% Communication
        </p>
    </div>
    """, unsafe_allow_html=True)

    # PDF download at top
    dl_col, info_col = st.columns([2, 5])
    with dl_col:
        try:
            pdf_bytes = generate_pdf(report)
            role_slug = report.role.lower().replace(" ", "_")[:20]
            st.download_button(
                "⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=f"interview_report_{role_slug}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"PDF unavailable: {e}")
    with info_col:
        st.markdown(
            '<p style="color:#64748b;font-size:0.82rem;padding-top:0.6rem;">Full report with all scores, AI notes, and improvement tips</p>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Strengths & Gaps ───────────────────────────────────────────────────
    str_col, gap_col = st.columns(2, gap="large")
    with str_col:
        st.markdown('<p style="font-weight:600;font-size:0.95rem;color:#1e293b;margin-bottom:0.5rem;">✅ Strengths</p>', unsafe_allow_html=True)
        for s in report.top_strengths:
            st.markdown(f'<div class="card-success"><p style="margin:0;font-size:0.875rem;color:#15803d;">• {s}</p></div>', unsafe_allow_html=True)
    with gap_col:
        st.markdown('<p style="font-weight:600;font-size:0.95rem;color:#1e293b;margin-bottom:0.5rem;">⚠️ Areas to Improve</p>', unsafe_allow_html=True)
        for g in report.top_gaps:
            st.markdown(f'<div class="card-warning"><p style="margin:0;font-size:0.875rem;color:#92400e;">• {g}</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Radar chart (LLM dimensions across all questions) ─────────────────
    llm_evals = [ev.llm_eval_score for ev in report.evaluations if ev.llm_eval_score]
    if llm_evals:
        avg_td = sum(l.technical_depth    for l in llm_evals) / len(llm_evals)
        avg_rq = sum(l.reasoning_quality  for l in llm_evals) / len(llm_evals)
        avg_ps = sum(l.problem_solving    for l in llm_evals) / len(llm_evals)
        avg_tt = sum(l.trade_off_thinking for l in llm_evals) / len(llm_evals)
        avg_am = sum(l.answer_maturity    for l in llm_evals) / len(llm_evals)

        dimensions = ["Technical Depth", "Reasoning Quality", "Problem Solving",
                      "Trade-off Thinking", "Answer Maturity"]
        values     = [avg_td, avg_rq, avg_ps, avg_tt, avg_am]

        radar_col, summary_col = st.columns([3, 2], gap="large")
        with radar_col:
            st.markdown('<p style="font-weight:600;font-size:0.95rem;color:#1e293b;margin-bottom:0.5rem;">🤖 AI Interviewer — Performance Radar</p>', unsafe_allow_html=True)
            fig = go.Figure(go.Scatterpolar(
                r=values + [values[0]],
                theta=dimensions + [dimensions[0]],
                fill="toself",
                fillcolor="rgba(99,102,241,0.15)",
                line=dict(color="#6366f1", width=2),
                marker=dict(size=6, color="#4f46e5"),
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=9), gridcolor="#e2e8f0"),
                    angularaxis=dict(tickfont=dict(size=9, color="#334155")),
                    bgcolor="white",
                ),
                showlegend=False,
                height=300,
                margin=dict(t=20, b=20, l=40, r=40),
                paper_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)

        with summary_col:
            st.markdown('<p style="font-weight:600;font-size:0.95rem;color:#1e293b;margin-bottom:0.75rem;">Dimension Scores</p>', unsafe_allow_html=True)
            for dim, val in zip(dimensions, values):
                colour = "#10b981" if val >= 7 else "#f59e0b" if val >= 5 else "#ef4444"
                st.markdown(f"""
                <div style="margin-bottom:0.6rem;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.15rem;">
                        <span style="font-size:0.78rem;color:#334155;">{dim}</span>
                        <span style="font-size:0.78rem;font-weight:600;color:{colour};">{val:.1f}/10</span>
                    </div>
                    <div style="background:#f1f5f9;border-radius:4px;height:5px;">
                        <div style="width:{val/10*100:.0f}%;height:100%;background:{colour};border-radius:4px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Per-question breakdown ─────────────────────────────────────────────
    st.markdown('<p style="font-weight:700;font-size:1.1rem;color:#0f172a;margin-bottom:1rem;">📋 Per-Question Breakdown</p>', unsafe_allow_html=True)

    for i, ev in enumerate(report.evaluations):
        qtxt   = ev.qa_pair.question.text
        qlabel = qtxt[:70] + ("..." if len(qtxt) > 70 else "")
        t_lbl, t_cls, t_hex = _tier_info(ev.composite_score)

        with st.expander(f"Q{i+1}: {qlabel}   •   {ev.composite_score:.0f}/100", expanded=(i == 0)):

            # Answer excerpt
            st.markdown(
                f'<p style="font-size:0.82rem;color:#64748b;font-style:italic;margin-bottom:1rem;">'
                f'"{ev.qa_pair.answer[:250]}{"..." if len(ev.qa_pair.answer) > 250 else ""}"</p>',
                unsafe_allow_html=True
            )

            # Score badge
            st.markdown(
                f'<span class="score-tier-badge {t_cls}" style="font-size:0.82rem;">'
                f'{ev.composite_score:.0f}/100 — {t_lbl}</span><br><br>',
                unsafe_allow_html=True
            )

            # ── Section 1: AI Interviewer ──────────────────────────────────
            if ev.llm_eval_score:
                llm = ev.llm_eval_score
                st.markdown('<div class="section-header"><span class="icon">🤖</span><h3>AI Interviewer Assessment</h3></div>', unsafe_allow_html=True)

                m1, m2, m3 = st.columns(3)
                for col, label, val in [
                    (m1, "Technical Depth",    llm.technical_depth),
                    (m2, "Reasoning Quality",  llm.reasoning_quality),
                    (m3, "Problem Solving",    llm.problem_solving),
                ]:
                    c = "#10b981" if val >= 7 else "#f59e0b" if val >= 5 else "#ef4444"
                    with col:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="color:{c};">{val:.1f}</div>
                            <div class="metric-label">{label}</div>
                            {_bar(val, 10, c)}
                        </div>
                        """, unsafe_allow_html=True)

                m4, m5, m6 = st.columns(3)
                for col, label, val in [
                    (m4, "Trade-off Thinking", llm.trade_off_thinking),
                    (m5, "Answer Maturity",    llm.answer_maturity),
                    (m6, "Overall LLM Score",  llm.overall_llm_score),
                ]:
                    c = "#10b981" if val >= 7 else "#f59e0b" if val >= 5 else "#ef4444"
                    with col:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="color:{c};">{val:.1f}</div>
                            <div class="metric-label">{label}</div>
                            {_bar(val, 10, c)}
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                for lbl, txt in [
                    ("Technical",  llm.technical_feedback),
                    ("Reasoning",  llm.reasoning_feedback),
                    ("Trade-offs", llm.trade_off_feedback),
                    ("Maturity",   llm.maturity_feedback),
                ]:
                    if txt:
                        st.markdown(f'<div class="feedback-item"><strong>{lbl}:</strong> {txt}</div>', unsafe_allow_html=True)

                if llm.interviewer_summary:
                    st.markdown(
                        f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:0.75rem 1rem;margin:0.5rem 0;">'
                        f'<p style="font-size:0.78rem;font-weight:600;color:#1d4ed8;margin:0 0 0.25rem;">💼 Interviewer Notes</p>'
                        f'<p style="font-size:0.85rem;color:#1e40af;margin:0;">{llm.interviewer_summary}</p></div>',
                        unsafe_allow_html=True
                    )

                if llm.follow_up_questions:
                    st.markdown('<p style="font-size:0.82rem;font-weight:600;color:#334155;margin:0.75rem 0 0.25rem;">An interviewer might ask:</p>', unsafe_allow_html=True)
                    for fq in llm.follow_up_questions:
                        st.markdown(f'<p style="font-size:0.82rem;color:#64748b;margin:0.1rem 0 0.1rem 0.75rem;">→ <em>{fq}</em></p>', unsafe_allow_html=True)

            # ── Section 2: Rule-Based ──────────────────────────────────────
            if ev.rule_based_score:
                rb = ev.rule_based_score
                st.markdown('<div class="section-header"><span class="icon">📊</span><h3>Objective Rule-Based Metrics</h3></div>', unsafe_allow_html=True)

                r1, r2, r3, r4, r5 = st.columns(5)
                for col, label, val, max_v in [
                    (r1, "Ownership",      rb.ownership_score,      10),
                    (r2, "Impact",         rb.impact_score,         10),
                    (r3, "Skill Coverage", rb.skill_coverage_pct,  100),
                    (r4, "STAR Structure", rb.star_structure_score, 10),
                    (r5, "Completeness",   rb.word_count_score,     10),
                ]:
                    display_val = f"{val:.0f}%" if max_v == 100 else f"{val:.1f}/10"
                    norm = val / max_v
                    c = "#10b981" if norm >= 0.7 else "#f59e0b" if norm >= 0.4 else "#ef4444"
                    with col:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="color:{c};font-size:1.2rem;">{display_val}</div>
                            <div class="metric-label">{label}</div>
                            {_bar(val, max_v, c)}
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Skills matched / missing as tags
                if rb.matched_skills:
                    st.markdown('<p style="font-size:0.78rem;font-weight:600;color:#334155;margin-bottom:0.25rem;">✅ Skills mentioned</p>', unsafe_allow_html=True)
                    tags = "".join(f'<span class="tag tag-green">{s}</span>' for s in rb.matched_skills[:8])
                    st.markdown(f'<div>{tags}</div>', unsafe_allow_html=True)

                if rb.missing_skills:
                    st.markdown('<p style="font-size:0.78rem;font-weight:600;color:#334155;margin:0.5rem 0 0.25rem;">❌ Not mentioned</p>', unsafe_allow_html=True)
                    tags = "".join(f'<span class="tag tag-red">{s}</span>' for s in rb.missing_skills[:8])
                    st.markdown(f'<div>{tags}</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                for fb in [rb.ownership_feedback, rb.impact_feedback, rb.skill_feedback,
                           rb.star_feedback, rb.completeness_feedback]:
                    if fb:
                        st.markdown(f'<div class="feedback-item">{fb}</div>', unsafe_allow_html=True)

            # ── Section 3: Communication ───────────────────────────────────
            comm = ev.communication
            st.markdown('<div class="section-header"><span class="icon">🗣️</span><h3>Communication Analysis</h3></div>', unsafe_allow_html=True)

            ca, cb, cc, cd = st.columns(4)
            for col, label, val, max_v in [
                (ca, "Comm Score",   comm.score,         10),
                (cb, "Reading Ease", comm.reading_ease,  100),
                (cc, "Filler Words", comm.filler_word_count, None),
                (cd, "Word Count",   comm.word_count,    None),
            ]:
                with col:
                    if max_v:
                        norm = val / max_v
                        c = "#10b981" if norm >= 0.6 else "#f59e0b" if norm >= 0.3 else "#ef4444"
                        bar = _bar(val, max_v, c)
                        display = f"{val:.1f}" if isinstance(val, float) else str(val)
                    else:
                        # Filler words / word count — lower filler = better
                        if label == "Filler Words":
                            c = "#10b981" if val == 0 else "#f59e0b" if val <= 3 else "#ef4444"
                        else:
                            c = "#10b981" if 80 <= val <= 200 else "#f59e0b"
                        bar = ""
                        display = str(int(val))
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color:{c};">{display}</div>
                        <div class="metric-label">{label}</div>
                        {bar}
                    </div>
                    """, unsafe_allow_html=True)

            # STAR sub-scores
            star = ev.star_score
            if star.total > 0:
                st.markdown('<p style="font-size:0.78rem;font-weight:600;color:#334155;margin:1rem 0 0.5rem;">STAR Method Scores (LLM-assessed)</p>', unsafe_allow_html=True)
                s1, s2, s3, s4 = st.columns(4)
                for col, label, val in [
                    (s1, "Situation", star.situation_score),
                    (s2, "Task",      star.task_score),
                    (s3, "Action",    star.action_score),
                    (s4, "Result",    star.result_score),
                ]:
                    c = "#10b981" if val >= 7 else "#f59e0b" if val >= 5 else "#ef4444"
                    with col:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value" style="color:{c};font-size:1.2rem;">{val:.1f}</div>
                            <div class="metric-label">{label}</div>
                            {_bar(val, 10, c)}
                        </div>
                        """, unsafe_allow_html=True)

            # ── Final score + tips ─────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:1rem 1.25rem;">'
                f'<p style="font-weight:700;font-size:1rem;color:{t_hex};margin:0 0 0.5rem;">'
                f'🏆 Final Score: {ev.composite_score:.0f}/100 — {t_lbl}</p>',
                unsafe_allow_html=True
            )
            if ev.improvement_tips:
                for tip in ev.improvement_tips:
                    st.markdown(f'<div class="tip-item">💡 {tip}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Recommended next steps ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p style="font-weight:700;font-size:1.1rem;color:#0f172a;margin-bottom:0.75rem;">🎯 Recommended Next Steps</p>', unsafe_allow_html=True)

    rec_cols = st.columns(min(len(report.practice_recommendations), 3))
    for i, rec in enumerate(report.practice_recommendations):
        with rec_cols[i % 3]:
            st.markdown(f"""
            <div class="card" style="text-align:center;padding:1.25rem;">
                <div style="font-size:1.5rem;margin-bottom:0.5rem;">{["📚","🎙️","📊","🔍","💬"][i % 5]}</div>
                <p style="font-size:0.82rem;color:#334155;line-height:1.5;margin:0;">{rec}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── New session CTA ────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    cta_l, cta_m, cta_r = st.columns([3, 2, 3])
    with cta_m:
        if st.button("🔄 New Interview Session", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    init_state()
    step = st.session_state.step
    if step == 0:
        render_landing()
    elif step == 1:
        render_step1()
    elif step == 2:
        render_step2()
    elif step == 3:
        render_step3()

main()
