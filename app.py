"""
app.py — AI Interview Coach
Premium dark theme — Linear/Vercel/OpenAI-inspired design
Backend untouched. Only app.py modified.
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objects as go

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

# ── Dark theme CSS ────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ─────────────────────────────────────────
   DESIGN TOKENS
───────────────────────────────────────── */
:root {
  --bg:          #080B16;
  --bg-2:        #0D1117;
  --card:        #111827;
  --card-2:      #1A2235;
  --card-3:      #1E293B;
  --border:      rgba(255,255,255,0.07);
  --border-2:    rgba(255,255,255,0.12);
  --primary:     #6366F1;
  --primary-d:   #4F46E5;
  --purple:      #8B5CF6;
  --cyan:        #22D3EE;
  --cyan-d:      #06B6D4;
  --success:     #10B981;
  --warning:     #F59E0B;
  --danger:      #EF4444;
  --text-1:      #F1F5F9;
  --text-2:      #94A3B8;
  --text-3:      #64748B;
  --glow-p:      rgba(99,102,241,0.25);
  --glow-c:      rgba(34,211,238,0.15);
}

/* ─────────────────────────────────────────
   BASE RESET — FORCE DARK EVERYWHERE
───────────────────────────────────────── */
html, body { background: var(--bg) !important; }

.stApp {
  background: var(--bg) !important;
  font-family: 'Inter', sans-serif !important;
}

.main, section[data-testid="stMain"],
.main .block-container,
div[data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
}

.main .block-container {
  padding: 1.5rem 2rem 4rem !important;
  max-width: 1120px !important;
}

/* Dark text defaults */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Inter', sans-serif !important;
  color: var(--text-1) !important;
}
p, li, span, label, div {
  font-family: 'Inter', sans-serif;
  color: var(--text-2);
}

/* ─────────────────────────────────────────
   HIDE STREAMLIT CHROME
───────────────────────────────────────── */
#MainMenu, footer, header,
[data-testid="stSidebarNav"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
  display: none !important;
  visibility: hidden !important;
}

/* ─────────────────────────────────────────
   GLASS CARD
───────────────────────────────────────── */
.glass {
  background: rgba(17,24,39,0.85);
  border: 1px solid var(--border);
  border-radius: 16px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 4px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04);
  padding: 1.5rem;
  margin-bottom: 1rem;
}
.glass-sm {
  background: rgba(17,24,39,0.85);
  border: 1px solid var(--border);
  border-radius: 12px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 2px 16px rgba(0,0,0,0.3);
  padding: 1rem 1.25rem;
  margin-bottom: 0.75rem;
}
.glass-accent {
  border-left: 3px solid var(--primary);
}
.glass-cyan {
  border-left: 3px solid var(--cyan);
}
.glass-success {
  border-left: 3px solid var(--success);
  background: rgba(16,185,129,0.06);
}
.glass-warning {
  border-left: 3px solid var(--warning);
  background: rgba(245,158,11,0.06);
}
.glass-danger {
  border-left: 3px solid var(--danger);
  background: rgba(239,68,68,0.06);
}

/* ─────────────────────────────────────────
   GRADIENT TEXT
───────────────────────────────────────── */
.gradient-text {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #22D3EE 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.gradient-text-ip {
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ─────────────────────────────────────────
   HERO
───────────────────────────────────────── */
.hero-wrap {
  text-align: center;
  padding: 4rem 2rem 3rem;
  position: relative;
  overflow: hidden;
}
.hero-wrap::before {
  content: '';
  position: absolute;
  top: -60px; left: 50%; transform: translateX(-50%);
  width: 600px; height: 300px;
  background: radial-gradient(ellipse, rgba(99,102,241,0.18) 0%, transparent 70%);
  pointer-events: none;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(99,102,241,0.15);
  border: 1px solid rgba(99,102,241,0.3);
  color: #A5B4FC;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.3rem 0.9rem;
  border-radius: 999px;
  margin-bottom: 1.5rem;
  display: inline-block;
}
.hero-title {
  font-size: 3.2rem;
  font-weight: 800;
  line-height: 1.1;
  margin: 0 0 1rem;
  letter-spacing: -0.02em;
}
.hero-sub {
  font-size: 1.1rem;
  color: var(--text-2);
  max-width: 560px;
  margin: 0 auto 2.5rem;
  line-height: 1.7;
}

/* ─────────────────────────────────────────
   FEATURE CARDS
───────────────────────────────────────── */
.feat-card {
  background: rgba(17,24,39,0.9);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.4rem;
  height: 100%;
  transition: border-color 0.2s;
}
.feat-card:hover { border-color: var(--border-2); }
.feat-icon {
  font-size: 1.6rem;
  margin-bottom: 0.75rem;
  display: block;
}
.feat-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--text-1) !important;
  margin-bottom: 0.35rem;
}
.feat-desc {
  font-size: 0.78rem;
  color: var(--text-3) !important;
  line-height: 1.55;
}

/* ─────────────────────────────────────────
   STEPPER
───────────────────────────────────────── */
.stepper {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.85rem 1.5rem;
  background: rgba(17,24,39,0.8);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 2rem;
  gap: 0;
}
.stp-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.stp-dot {
  width: 26px; height: 26px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700;
  flex-shrink: 0;
}
.stp-active  { background: linear-gradient(135deg,#6366F1,#8B5CF6); color: white; box-shadow: 0 0 12px var(--glow-p); }
.stp-done    { background: var(--success); color: white; }
.stp-pending { background: rgba(255,255,255,0.06); color: var(--text-3); border: 1px solid var(--border); }
.stp-label   { font-size: 0.8rem; font-weight: 500; }
.stp-active-lbl  { color: #A5B4FC; }
.stp-done-lbl    { color: var(--success); }
.stp-pending-lbl { color: var(--text-3); }
.stp-line { width: 44px; height: 1px; background: var(--border); margin: 0 0.35rem; }
.stp-line-done   { background: var(--success); }

/* ─────────────────────────────────────────
   PILLS / TAGS
───────────────────────────────────────── */
.pill {
  display: inline-block;
  background: rgba(99,102,241,0.15);
  border: 1px solid rgba(99,102,241,0.3);
  color: #A5B4FC;
  font-size: 0.72rem; font-weight: 500;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  margin: 0.15rem;
}
.pill-cyan {
  background: rgba(34,211,238,0.12);
  border-color: rgba(34,211,238,0.25);
  color: #67E8F9;
}
.pill-green {
  background: rgba(16,185,129,0.12);
  border-color: rgba(16,185,129,0.25);
  color: #6EE7B7;
}
.pill-red {
  background: rgba(239,68,68,0.12);
  border-color: rgba(239,68,68,0.25);
  color: #FCA5A5;
}
.pill-amber {
  background: rgba(245,158,11,0.12);
  border-color: rgba(245,158,11,0.25);
  color: #FCD34D;
}
.pill-type-b { background:rgba(99,102,241,0.15);  border:1px solid rgba(99,102,241,0.3);  color:#A5B4FC; font-size:0.7rem; font-weight:600; padding:0.18rem 0.6rem; border-radius:999px; letter-spacing:0.04em; text-transform:uppercase; }
.pill-type-t { background:rgba(34,211,238,0.12);  border:1px solid rgba(34,211,238,0.25); color:#67E8F9; font-size:0.7rem; font-weight:600; padding:0.18rem 0.6rem; border-radius:999px; letter-spacing:0.04em; text-transform:uppercase; }
.pill-type-s { background:rgba(245,158,11,0.12);  border:1px solid rgba(245,158,11,0.25); color:#FCD34D; font-size:0.7rem; font-weight:600; padding:0.18rem 0.6rem; border-radius:999px; letter-spacing:0.04em; text-transform:uppercase; }
.pill-type-c { background:rgba(16,185,129,0.12);  border:1px solid rgba(16,185,129,0.25); color:#6EE7B7; font-size:0.7rem; font-weight:600; padding:0.18rem 0.6rem; border-radius:999px; letter-spacing:0.04em; text-transform:uppercase; }

/* ─────────────────────────────────────────
   METRIC CARD
───────────────────────────────────────── */
.m-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.85rem 0.75rem;
  text-align: center;
  margin-bottom: 0.5rem;
}
.m-val {
  font-size: 1.4rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 0.2rem;
  display: block;
}
.m-lbl {
  font-size: 0.72rem;
  color: var(--text-3);
  line-height: 1.3;
  display: block;
}
.m-bar-wrap {
  height: 3px;
  background: rgba(255,255,255,0.06);
  border-radius: 2px;
  margin-top: 0.45rem;
  overflow: hidden;
}
.m-bar-fill { height: 100%; border-radius: 2px; }

/* ─────────────────────────────────────────
   SECTION HEADER
───────────────────────────────────────── */
.sec-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 1.5rem 0 0.85rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--border);
}
.sec-head-icon { font-size: 1.05rem; }
.sec-head-title {
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  color: var(--text-1) !important;
  margin: 0 !important;
  letter-spacing: 0.02em;
}

/* ─────────────────────────────────────────
   FEEDBACK ITEMS
───────────────────────────────────────── */
.fb-item {
  background: var(--card-2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--primary);
  border-radius: 8px;
  padding: 0.65rem 0.9rem;
  margin-bottom: 0.45rem;
  font-size: 0.82rem;
  color: var(--text-2) !important;
  line-height: 1.6;
}
.fb-item strong { color: var(--text-1) !important; }

.tip-item {
  background: rgba(245,158,11,0.08);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: 8px;
  padding: 0.65rem 0.9rem;
  margin-bottom: 0.45rem;
  font-size: 0.82rem;
  color: #FCD34D !important;
  line-height: 1.6;
}

.note-cyan {
  background: rgba(34,211,238,0.07);
  border: 1px solid rgba(34,211,238,0.18);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin: 0.5rem 0;
}

/* ─────────────────────────────────────────
   SCORE HERO CARD
───────────────────────────────────────── */
.score-hero {
  background: linear-gradient(135deg, #111827 0%, #1A2235 50%, #111827 100%);
  border: 1px solid var(--border-2);
  border-radius: 20px;
  padding: 2.5rem 2rem;
  text-align: center;
  position: relative;
  overflow: hidden;
  margin-bottom: 1.5rem;
  box-shadow: 0 8px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05);
}
.score-hero::before {
  content: '';
  position: absolute;
  top: -80px; left: 50%; transform: translateX(-50%);
  width: 400px; height: 200px;
  background: radial-gradient(ellipse, rgba(99,102,241,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.score-num {
  font-size: 5.5rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.04em;
}
.score-subtitle {
  font-size: 0.82rem;
  color: var(--text-3) !important;
  margin-top: 0.5rem;
}

/* ─────────────────────────────────────────
   PROGRESS DOTS
───────────────────────────────────────── */
.pdots { display: flex; gap: 0.35rem; margin-bottom: 0.5rem; align-items: center; }
.pd { width: 8px; height: 8px; border-radius: 50%; }
.pd-done    { background: var(--success); }
.pd-current { background: var(--primary); box-shadow: 0 0 6px var(--glow-p); }
.pd-pending { background: rgba(255,255,255,0.1); }

/* ─────────────────────────────────────────
   QUESTION CARD
───────────────────────────────────────── */
.q-card {
  background: rgba(17,24,39,0.9);
  border: 1px solid var(--border);
  border-left: 4px solid var(--primary);
  border-radius: 14px;
  padding: 1.75rem;
  margin: 1rem 0;
  box-shadow: 0 0 24px var(--glow-p);
}
.q-text {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-1) !important;
  line-height: 1.55;
  margin-top: 0.6rem;
}

/* ─────────────────────────────────────────
   STREAMLIT WIDGET OVERRIDES
───────────────────────────────────────── */

/* Text area */
.stTextArea > label { color: var(--text-2) !important; font-size: 0.82rem !important; }
.stTextArea textarea {
  background: var(--card) !important;
  border: 1px solid var(--border-2) !important;
  border-radius: 10px !important;
  color: var(--text-1) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.9rem !important;
  line-height: 1.65 !important;
  caret-color: var(--primary);
}
.stTextArea textarea:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
  outline: none !important;
}
.stTextArea textarea::placeholder { color: var(--text-3) !important; }

/* Buttons */
.stButton > button {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  border-radius: 9px !important;
  transition: all 0.15s ease !important;
  border: none !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
  color: white !important;
  box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important;
  transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--text-2) !important;
  border: 1px solid var(--border-2) !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: var(--primary) !important;
  color: #A5B4FC !important;
}

/* Download button */
.stDownloadButton > button {
  background: linear-gradient(135deg, #10B981, #059669) !important;
  color: white !important;
  font-weight: 600 !important;
  border-radius: 9px !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(16,185,129,0.3) !important;
}

/* Slider */
.stSlider > label { color: var(--text-2) !important; font-size: 0.82rem !important; }
.stSlider [data-baseweb="slider"] [role="slider"] { background: var(--primary) !important; }
.stSlider [data-baseweb="slider"] [data-testid="stSliderTrack"] > div:first-child { background: var(--border) !important; }
.stSlider [data-baseweb="slider"] [data-testid="stSliderTrack"] > div:last-child { background: var(--primary) !important; }

/* Radio */
.stRadio > label { color: var(--text-2) !important; font-size: 0.82rem !important; }
.stRadio [data-baseweb="radio"] { background: transparent !important; }
.stRadio label { color: var(--text-2) !important; font-size: 0.87rem !important; }
[data-baseweb="radio"] [class*="radioMarkOuter"] { border-color: var(--border-2) !important; background: var(--card) !important; }
[data-baseweb="radio"] input:checked ~ [class*="radioMarkOuter"] { border-color: var(--primary) !important; }
[data-baseweb="radio"] [class*="radioMarkInner"] { background: var(--primary) !important; }

/* Expander */
.streamlit-expanderHeader {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--text-1) !important;
  font-weight: 500 !important;
  font-size: 0.88rem !important;
}
.streamlit-expanderHeader:hover { border-color: var(--border-2) !important; }
.streamlit-expanderContent {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 10px 10px !important;
  padding: 1rem !important;
}
[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  margin-bottom: 0.5rem !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, var(--primary), var(--purple)) !important;
}
.stProgress > div > div { background: rgba(255,255,255,0.06) !important; border-radius: 4px !important; }

/* Status widget */
[data-testid="stStatusWidget"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; }

/* Metrics */
[data-testid="stMetricValue"] { color: var(--text-1) !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: var(--text-3) !important; font-size: 0.78rem !important; }

/* Select box */
.stSelectbox > label { color: var(--text-2) !important; font-size: 0.82rem !important; }
[data-baseweb="select"] > div {
  background: var(--card) !important;
  border-color: var(--border-2) !important;
  border-radius: 9px !important;
  color: var(--text-1) !important;
}

/* HR */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* Divider text */
.or-divider {
  text-align: center;
  color: var(--text-3);
  font-size: 0.78rem;
  margin: 0.4rem 0;
  position: relative;
}

/* Columns gap */
[data-testid="column"] { padding: 0 0.4rem !important; }
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
def get_jd_parser():    return JDParser()
@st.cache_resource
def get_question_generator(): return QuestionGenerator()
@st.cache_resource
def get_evaluation_engine():  return EvaluationEngine()

# ── Session state ─────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "step": 0,
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

# ── Helpers ───────────────────────────────────────────────────────────────────

def _tier(score: float):
    if score >= 75: return "Excellent", "#10B981", "pill-green"
    if score >= 50: return "Good",      "#F59E0B", "pill-amber"
    return "Needs Work", "#EF4444", "pill-red"

def _colour(norm: float) -> str:
    if norm >= 0.7: return "#10B981"
    if norm >= 0.4: return "#F59E0B"
    return "#EF4444"

def _mcard(label: str, value: str, norm: float) -> str:
    c   = _colour(norm)
    pct = min(norm * 100, 100)
    return f"""
<div class="m-card">
  <span class="m-val" style="color:{c};">{value}</span>
  <span class="m-lbl">{label}</span>
  <div class="m-bar-wrap"><div class="m-bar-fill" style="width:{pct:.0f}%;background:{c};"></div></div>
</div>"""

def _bar_row(label: str, val: float, max_val: float = 10.0) -> str:
    norm = val / max_val
    c    = _colour(norm)
    pct  = min(norm * 100, 100)
    disp = f"{val:.0f}%" if max_val == 100 else f"{val:.1f}"
    return f"""
<div style="margin-bottom:0.55rem;">
  <div style="display:flex;justify-content:space-between;margin-bottom:0.2rem;">
    <span style="font-size:0.78rem;color:#94A3B8;">{label}</span>
    <span style="font-size:0.78rem;font-weight:600;color:{c};">{disp}</span>
  </div>
  <div style="background:rgba(255,255,255,0.06);border-radius:3px;height:4px;overflow:hidden;">
    <div style="width:{pct:.0f}%;height:100%;background:{c};border-radius:3px;"></div>
  </div>
</div>"""

# ── Top nav ───────────────────────────────────────────────────────────────────

def render_topnav():
    c1, c2, c3 = st.columns([3, 6, 2])
    with c1:
        st.markdown(
            '<p style="font-size:1rem;font-weight:700;margin:0;padding-top:0.3rem;'
            'background:linear-gradient(135deg,#6366F1,#22D3EE);'
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
            '🎯 AI Interview Coach</p>',
            unsafe_allow_html=True,
        )
    with c3:
        if st.session_state.step > 0:
            if st.button("↩ Restart", key="nav_restart"):
                for k in list(st.session_state.keys()): del st.session_state[k]
                st.rerun()
    st.markdown('<hr style="margin:0.6rem 0 1.75rem;border:none;border-top:1px solid rgba(255,255,255,0.07);">',
                unsafe_allow_html=True)

# ── Stepper ───────────────────────────────────────────────────────────────────

def render_stepper():
    step   = st.session_state.step
    labels = ["Job Setup", "Mock Interview", "Report"]
    parts  = []
    for i, lbl in enumerate(labels, 1):
        if i < step:
            dc, lc = "stp-done",    "stp-done-lbl";    inner = "✓"
        elif i == step:
            dc, lc = "stp-active",  "stp-active-lbl";  inner = str(i)
        else:
            dc, lc = "stp-pending", "stp-pending-lbl"; inner = str(i)
        parts.append(f'<div class="stp-item"><div class="stp-dot {dc}">{inner}</div>'
                     f'<span class="stp-label {lc}">{lbl}</span></div>')
        if i < len(labels):
            lc2 = "stp-line-done" if i < step else ""
            parts.append(f'<div class="stp-line {lc2}"></div>')
    st.markdown(f'<div class="stepper">{"".join(parts)}</div>', unsafe_allow_html=True)

# ── SCREEN 0: Landing ─────────────────────────────────────────────────────────

def render_landing():
    render_topnav()

    st.markdown("""
    <div class="hero-wrap">
      <div class="hero-badge">✦ AI-Powered Interview Preparation</div>
      <h1 class="hero-title">
        <span class="gradient-text">AI Interview Coach</span>
      </h1>
      <p class="hero-sub">
        Practice smarter. Improve faster. Crack your next interview.<br>
        Generate role-specific questions, answer them, and receive a detailed
        hybrid AI evaluation across 10 dimensions.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # CTA buttons
    b1, b2, b3, b4, b5 = st.columns([1.5, 1.5, 0.5, 1.5, 1.5])
    with b2:
        if st.button("🚀 Start Interview", type="primary",
                     use_container_width=True, key="land_start"):
            st.session_state.step = 1
            st.session_state.demo_mode = False
            st.rerun()
    with b4:
        if st.button("⚡ Try Demo", use_container_width=True, key="land_demo"):
            st.session_state.step        = 1
            st.session_state.demo_mode   = True
            st.session_state.jd_text     = SAMPLE_JD
            st.session_state.n_questions = 2
            st.rerun()

    st.markdown('<p class="or-divider" style="margin:0.2rem 0 0.75rem;">Start a full session or try a 2-question demo instantly</p>',
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature cards
    fc1, fc2, fc3, fc4 = st.columns(4, gap="small")
    for col, icon, title, desc in [
        (fc1, "🤖", "AI Interviewer",
         "Gemini acts as a senior engineer scoring technical depth, reasoning, trade-offs, and answer maturity"),
        (fc2, "📊", "Rule-Based Scoring",
         "Deterministic signals check ownership language, quantified impact, and JD skill coverage — zero LLM cost"),
        (fc3, "🗣️", "Communication Intel",
         "spaCy measures reading clarity, filler words, passive voice, and vocabulary diversity"),
        (fc4, "📄", "PDF Report",
         "Download a full readiness report with explainable scores, AI notes, and improvement tips"),
    ]:
        with col:
            st.markdown(f"""
            <div class="feat-card">
              <span class="feat-icon">{icon}</span>
              <p class="feat-title">{title}</p>
              <p class="feat-desc">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(255,255,255,0.07);">', unsafe_allow_html=True)

    # How it works
    st.markdown(
        '<p style="text-align:center;font-weight:600;font-size:0.95rem;'
        'color:#F1F5F9;margin-bottom:1.25rem;letter-spacing:0.02em;">How it works</p>',
        unsafe_allow_html=True)
    h1, h2, h3, h4 = st.columns(4, gap="small")
    for col, num, title, desc, c in [
        (h1, "01", "Paste JD", "Paste any job description — we extract role, skills, and tech stack", "#6366F1"),
        (h2, "02", "Set Mode", "Choose Technical, Behavioural, or Mixed and pick question count",    "#8B5CF6"),
        (h3, "03", "Answer",   "Answer role-specific questions one at a time in a guided session",   "#22D3EE"),
        (h4, "04", "Report",   "Get a 4-section hybrid evaluation with a downloadable PDF",          "#10B981"),
    ]:
        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:1.1rem 0.5rem;">
              <div style="width:36px;height:36px;border-radius:10px;background:rgba(255,255,255,0.05);
                          border:1px solid rgba(255,255,255,0.08);color:{c};font-size:0.78rem;
                          font-weight:700;display:flex;align-items:center;justify-content:center;
                          margin:0 auto 0.75rem;">{num}</div>
              <p style="font-weight:600;font-size:0.85rem;color:#F1F5F9;margin-bottom:0.3rem;">{title}</p>
              <p style="font-size:0.75rem;color:#64748B;line-height:1.5;margin:0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

# ── SCREEN 1: Job Setup ───────────────────────────────────────────────────────

def render_step1():
    render_topnav()
    render_stepper()

    st.markdown('<h2 style="font-size:1.5rem;font-weight:700;margin-bottom:0.25rem;color:#F1F5F9;">Set Up Your Session</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748B;margin-bottom:1.75rem;font-size:0.88rem;">Paste a job description — we\'ll extract the role and generate tailored interview questions.</p>', unsafe_allow_html=True)

    if st.session_state.demo_mode:
        st.markdown("""
        <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);
                    border-radius:10px;padding:0.65rem 1rem;margin-bottom:1rem;display:flex;align-items:center;gap:0.5rem;">
          <span style="font-size:0.8rem;font-weight:600;color:#A5B4FC;">⚡ Demo Mode</span>
          <span style="font-size:0.78rem;color:#6366F1;"> — Sample Backend Engineer JD is pre-loaded. 2 questions selected.</span>
        </div>
        """, unsafe_allow_html=True)

    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown('<div class="glass glass-accent">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.82rem;font-weight:600;color:#94A3B8;margin-bottom:0.6rem;letter-spacing:0.04em;text-transform:uppercase;">📋 Job Description</p>', unsafe_allow_html=True)

        sc, cl = st.columns([2, 1])
        with sc:
            if st.button("Use sample JD", key="sample_btn"):
                st.session_state.jd_text = SAMPLE_JD
                st.session_state["jd_ta"] = SAMPLE_JD
        with cl:
            if st.button("Clear", key="clear_btn"):
                st.session_state.jd_text = ""
                st.session_state["jd_ta"] = ""

        jd_text = st.text_area(
            "jd",
            value=st.session_state.jd_text,
            height=290,
            placeholder="Paste job description here — the more detail, the better your questions...",
            key="jd_ta",
            label_visibility="collapsed",
        )
        st.session_state.jd_text = jd_text

        char_c = "#10B981" if len(jd_text) > 100 else "#64748B"
        st.markdown(f'<p style="font-size:0.72rem;color:{char_c};text-align:right;margin-top:-0.4rem;">{len(jd_text)} characters</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        # Mode selector
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.82rem;font-weight:600;color:#94A3B8;margin-bottom:0.65rem;letter-spacing:0.04em;text-transform:uppercase;">🎯 Interview Mode</p>', unsafe_allow_html=True)
        mode = st.radio(
            "mode",
            ["Mixed", "Behavioural Only", "Technical Only"],
            index=["Mixed", "Behavioural Only", "Technical Only"].index(
                st.session_state.get("interview_mode", "Mixed")),
            key="mode_radio",
            label_visibility="collapsed",
        )
        st.session_state.interview_mode = mode
        mode_desc = {
            "Mixed":            "All types: behavioural, technical, situational, culture fit",
            "Behavioural Only": "Past experience and STAR-format situational answers",
            "Technical Only":   "System design, problem-solving, and technical depth",
        }
        st.markdown(f'<p style="font-size:0.75rem;color:#64748B;margin-top:0.25rem;">{mode_desc[mode]}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Questions
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.82rem;font-weight:600;color:#94A3B8;margin-bottom:0.5rem;letter-spacing:0.04em;text-transform:uppercase;">❓ Questions</p>', unsafe_allow_html=True)
        n = st.slider("n", 1, 10, st.session_state.n_questions,
                      label_visibility="collapsed", key="q_sl")
        st.session_state.n_questions = n
        st.markdown(f'<p style="font-size:0.75rem;color:#64748B;">Estimated time: <strong style="color:#94A3B8;">{n*3}–{n*5} minutes</strong></p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    gc1, gc2, gc3 = st.columns([3, 2, 3])
    with gc2:
        go_btn = st.button("Generate Questions →", type="primary",
                           use_container_width=True, key="gen_btn")

    if go_btn:
        txt = st.session_state.jd_text.strip()
        if len(txt) < 20:
            st.error("Please paste a job description (at least 20 characters).")
            return
        with st.spinner("Parsing job description..."):
            parser    = get_jd_parser()
            parsed_jd = parser.parse(txt)
            st.session_state.parsed_jd = parsed_jd

        with st.spinner("Generating questions with Gemini..."):
            gen  = get_question_generator()
            bank = gen.generate(parsed_jd)
            m    = st.session_state.interview_mode
            if m == "Behavioural Only":
                qs = [q for q in bank.questions if q.type.value in ("behavioural", "situational")]
            elif m == "Technical Only":
                qs = [q for q in bank.questions if q.type.value == "technical"]
            else:
                qs = bank.questions
            bank.questions = (qs or bank.questions)[:n]
            st.session_state.question_bank = bank

        st.session_state.step          = 2
        st.session_state.current_q_idx = 0
        st.session_state.answers       = {}
        st.session_state.report        = None
        st.rerun()

# ── SCREEN 2: Mock Interview ──────────────────────────────────────────────────

def render_step2():
    render_topnav()
    render_stepper()

    bank  = st.session_state.question_bank
    total = len(bank.questions)
    idx   = st.session_state.current_q_idx

    if idx >= total:
        qa = [QAPair(question=bank.questions[i], answer=a.strip())
              for i, a in st.session_state.answers.items()
              if a.strip() and i < total]
        st.session_state.qa_pairs = qa
        st.session_state.step     = 3
        st.rerun()
        return

    q = bank.questions[idx]

    # Top bar
    tb1, tb2 = st.columns([5, 2])
    with tb1:
        dots = "".join(
            f'<div class="pd pd-done"></div>'    if i < idx else
            f'<div class="pd pd-current"></div>' if i == idx else
            f'<div class="pd pd-pending"></div>'
            for i in range(total)
        )
        st.markdown(f'<div class="pdots">{dots}</div>', unsafe_allow_html=True)
    with tb2:
        st.markdown(
            f'<p style="text-align:right;font-size:0.82rem;color:#64748B;font-weight:500;margin:0;">'
            f'Question <strong style="color:#A5B4FC;">{idx+1}</strong> of {total}</p>',
            unsafe_allow_html=True)

    st.progress(idx / total)

    # Question card
    type_pill = {
        "behavioural":  ('pill-type-b', 'Behavioural'),
        "technical":    ('pill-type-t', 'Technical'),
        "situational":  ('pill-type-s', 'Situational'),
        "culture_fit":  ('pill-type-c', 'Culture Fit'),
    }.get(q.type.value, ('pill-type-b', q.type.value.title()))

    st.markdown(f"""
    <div class="q-card">
      <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.65rem;">
        <span class="{type_pill[0]}">{type_pill[1]}</span>
        <span style="font-size:0.7rem;color:#64748B;">· {q.difficulty} · STAR applicable: {'yes' if q.star_applicable else 'no'}</span>
      </div>
      <div class="q-text">{q.text}</div>
    </div>
    """, unsafe_allow_html=True)

    # STAR hint
    if q.star_applicable:
        st.markdown("""
        <div style="background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.15);
                    border-radius:8px;padding:0.65rem 1rem;margin-bottom:0.75rem;">
          <p style="font-size:0.75rem;font-weight:600;color:#A5B4FC;margin:0 0 0.25rem;">💡 STAR Framework</p>
          <p style="font-size:0.75rem;color:#64748B;margin:0;line-height:1.6;">
            <strong style="color:#94A3B8;">Situation</strong> — context &nbsp;·&nbsp;
            <strong style="color:#94A3B8;">Task</strong> — your goal &nbsp;·&nbsp;
            <strong style="color:#94A3B8;">Action</strong> — what YOU did (use "I") &nbsp;·&nbsp;
            <strong style="color:#94A3B8;">Result</strong> — measurable outcome
          </p>
        </div>
        """, unsafe_allow_html=True)

    # Answer area
    answer = st.text_area(
        "answer",
        value=st.session_state.answers.get(idx, ""),
        height=210,
        placeholder="Structure your answer clearly. Use 'I', not 'we'. Include specific actions and measurable results...",
        key=f"ans_{idx}",
        label_visibility="collapsed",
    )
    st.session_state.answers[idx] = answer

    wc = len(answer.split()) if answer.strip() else 0
    wc_c = "#10B981" if 80 <= wc <= 200 else "#F59E0B" if wc > 0 else "#64748B"
    wc_hint = "good length ✓" if 80 <= wc <= 200 else "aim for 80–200 words"
    st.markdown(
        f'<p style="font-size:0.72rem;color:{wc_c};text-align:right;margin-top:-0.3rem;">'
        f'{wc} words — {wc_hint}</p>',
        unsafe_allow_html=True)

    # Nav
    n1, n2, n3 = st.columns([1, 6, 1])
    with n1:
        if idx > 0 and st.button("← Back", key=f"bk_{idx}"):
            st.session_state.current_q_idx -= 1; st.rerun()
    with n3:
        label = "Finish ✓" if idx == total - 1 else "Next →"
        if st.button(label, type="primary", key=f"nx_{idx}"):
            if not answer.strip():
                st.warning("Please write an answer before continuing.")
            else:
                st.session_state.current_q_idx += 1; st.rerun()

# ── SCREEN 3: Report Dashboard ────────────────────────────────────────────────

def render_step3():
    render_topnav()
    render_stepper()

    # Evaluate
    if st.session_state.report is None:
        qa        = st.session_state.qa_pairs
        parsed_jd = st.session_state.parsed_jd
        if not qa:
            st.error("No answers found — please complete the mock interview first.")
            if st.button("← Back"): st.session_state.step = 2; st.rerun()
            return
        with st.status("🤖 Running hybrid evaluation...", expanded=True) as status:
            st.write("**1/3** AI Interviewer Assessment (Gemini)...")
            st.write("**2/3** Rule-based scoring — ownership · impact · skill coverage...")
            st.write("**3/3** Communication analysis — spaCy + textstat...")
            engine = get_evaluation_engine()
            evals  = engine.evaluate_all(qa, parsed_jd=parsed_jd)
            report = ReadinessReport.from_evaluations(evals, parsed_jd)
            st.session_state.report = report
            status.update(label="✅ Evaluation complete!", state="complete")

    report: ReadinessReport = st.session_state.report
    t_lbl, t_hex, t_pill    = _tier(report.overall_score)
    n_q                     = len(report.evaluations)

    # ── Hero score card ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="score-hero">
      <p style="color:#64748B;font-size:0.8rem;font-weight:500;margin:0 0 0.5rem;">
        {report.role} &nbsp;·&nbsp; {n_q} question{"s" if n_q!=1 else ""} evaluated
      </p>
      <div class="score-num" style="color:{t_hex};">{report.overall_score:.0f}</div>
      <p style="color:#64748B;font-size:0.82rem;margin:0.15rem 0 0.6rem;">out of 100</p>
      <span class="{t_pill}" style="font-size:0.82rem;font-weight:600;padding:0.3rem 1rem;">{t_lbl}</span>
      <p style="color:#475569;font-size:0.72rem;margin-top:0.85rem;letter-spacing:0.02em;">
        Composite: 40% AI Interviewer · 35% Rule-Based Metrics · 25% Communication
      </p>
    </div>
    """, unsafe_allow_html=True)

    # PDF + summary row
    dl_c, s1, s2, s3 = st.columns([2, 1, 1, 1])
    with dl_c:
        try:
            pdf = generate_pdf(report)
            slug = report.role.lower().replace(" ", "_")[:20]
            st.download_button("⬇️ Download PDF Report", data=pdf,
                               file_name=f"report_{slug}.pdf",
                               mime="application/pdf", use_container_width=True)
        except Exception as e:
            st.warning(f"PDF error: {e}")

    # Quick summary metrics
    llm_evals = [ev.llm_eval_score for ev in report.evaluations if ev.llm_eval_score]
    avg_llm   = sum(l.overall_llm_score for l in llm_evals) / len(llm_evals) if llm_evals else 0
    rb_evals  = [ev.rule_based_score for ev in report.evaluations if ev.rule_based_score]
    avg_skill = sum(r.skill_coverage_pct for r in rb_evals) / len(rb_evals) if rb_evals else 0
    comm_evals= [ev.communication for ev in report.evaluations]
    avg_comm  = sum(c.score for c in comm_evals) / len(comm_evals) if comm_evals else 0

    for col, label, val, suffix in [
        (s1, "AI Score",       avg_llm,   "/10"),
        (s2, "Skill Coverage", avg_skill, "%"),
        (s3, "Comm Score",     avg_comm,  "/10"),
    ]:
        with col:
            c = _colour(val/10 if suffix != "%" else val/100)
            st.markdown(f"""
            <div class="m-card" style="margin-top:0.1rem;">
              <span class="m-val" style="color:{c};font-size:1.2rem;">{val:.1f}{suffix}</span>
              <span class="m-lbl">{label}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown('<hr style="border-color:rgba(255,255,255,0.07);margin:1.25rem 0;">', unsafe_allow_html=True)

    # ── Strengths & Gaps ───────────────────────────────────────────────────
    sc, gc = st.columns(2, gap="large")
    with sc:
        st.markdown('<p style="font-size:0.88rem;font-weight:600;color:#F1F5F9;margin-bottom:0.6rem;">✅ Strengths</p>', unsafe_allow_html=True)
        for s in report.top_strengths:
            st.markdown(f'<div class="glass-sm glass-success"><p style="margin:0;font-size:0.82rem;color:#6EE7B7;">• {s}</p></div>', unsafe_allow_html=True)
    with gc:
        st.markdown('<p style="font-size:0.88rem;font-weight:600;color:#F1F5F9;margin-bottom:0.6rem;">⚠️ Areas to Improve</p>', unsafe_allow_html=True)
        for g in report.top_gaps:
            st.markdown(f'<div class="glass-sm glass-warning"><p style="margin:0;font-size:0.82rem;color:#FCD34D;">• {g}</p></div>', unsafe_allow_html=True)

    st.markdown('<hr style="border-color:rgba(255,255,255,0.07);margin:1.25rem 0;">', unsafe_allow_html=True)

    # ── Radar chart ────────────────────────────────────────────────────────
    if llm_evals:
        dims = ["Technical\nDepth", "Reasoning\nQuality", "Problem\nSolving",
                "Trade-off\nThinking", "Answer\nMaturity"]
        vals = [
            sum(l.technical_depth    for l in llm_evals) / len(llm_evals),
            sum(l.reasoning_quality  for l in llm_evals) / len(llm_evals),
            sum(l.problem_solving    for l in llm_evals) / len(llm_evals),
            sum(l.trade_off_thinking for l in llm_evals) / len(llm_evals),
            sum(l.answer_maturity    for l in llm_evals) / len(llm_evals),
        ]
        dims_clean = ["Technical Depth", "Reasoning Quality", "Problem Solving",
                      "Trade-off Thinking", "Answer Maturity"]

        rc, bc = st.columns([3, 2], gap="large")
        with rc:
            st.markdown('<p style="font-size:0.88rem;font-weight:600;color:#F1F5F9;margin-bottom:0.5rem;">🤖 AI Interviewer — Performance Radar</p>', unsafe_allow_html=True)
            fig = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=dims_clean + [dims_clean[0]],
                fill="toself",
                fillcolor="rgba(99,102,241,0.12)",
                line=dict(color="#6366F1", width=2),
                marker=dict(size=5, color="#8B5CF6"),
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor="#111827",
                    radialaxis=dict(
                        visible=True, range=[0, 10],
                        tickfont=dict(size=8, color="#64748B"),
                        gridcolor="rgba(255,255,255,0.06)",
                        linecolor="rgba(255,255,255,0.06)",
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=8, color="#94A3B8"),
                        gridcolor="rgba(255,255,255,0.06)",
                        linecolor="rgba(255,255,255,0.06)",
                    ),
                ),
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                showlegend=False,
                height=300,
                margin=dict(t=20, b=20, l=40, r=40),
            )
            st.plotly_chart(fig, use_container_width=True)

        with bc:
            st.markdown('<p style="font-size:0.88rem;font-weight:600;color:#F1F5F9;margin-bottom:0.85rem;">Dimension Breakdown</p>', unsafe_allow_html=True)
            for d, v in zip(dims_clean, vals):
                st.markdown(_bar_row(d, v, 10), unsafe_allow_html=True)

    st.markdown('<hr style="border-color:rgba(255,255,255,0.07);margin:1.25rem 0;">', unsafe_allow_html=True)

    # ── Per-question breakdown ─────────────────────────────────────────────
    st.markdown('<p style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:1rem;">📋 Per-Question Breakdown</p>', unsafe_allow_html=True)

    for i, ev in enumerate(report.evaluations):
        qtxt  = ev.qa_pair.question.text
        qlbl  = qtxt[:68] + ("…" if len(qtxt) > 68 else "")
        tl, th, tp = _tier(ev.composite_score)

        with st.expander(f"Q{i+1}: {qlbl}   ·   {ev.composite_score:.0f}/100 — {tl}", expanded=(i == 0)):

            # Answer excerpt
            st.markdown(
                f'<p style="font-size:0.8rem;color:#64748B;font-style:italic;margin-bottom:0.75rem;">'
                f'"{ev.qa_pair.answer[:280]}{"…" if len(ev.qa_pair.answer) > 280 else ""}"</p>',
                unsafe_allow_html=True)

            st.markdown(
                f'<span class="{tp}" style="font-size:0.78rem;font-weight:600;padding:0.25rem 0.8rem;">'
                f'{ev.composite_score:.0f}/100 — {tl}</span>',
                unsafe_allow_html=True)

            # ── AI Interviewer ─────────────────────────────────────────────
            if ev.llm_eval_score:
                llm = ev.llm_eval_score
                st.markdown('<div class="sec-head"><span class="sec-head-icon">🤖</span><p class="sec-head-title">AI Interviewer Assessment</p></div>', unsafe_allow_html=True)

                r1c1, r1c2, r1c3 = st.columns(3)
                for col, lbl, val in [
                    (r1c1, "Technical Depth",   llm.technical_depth),
                    (r1c2, "Reasoning Quality", llm.reasoning_quality),
                    (r1c3, "Problem Solving",   llm.problem_solving),
                ]:
                    with col: st.markdown(_mcard(lbl, f"{val:.1f}/10", val/10), unsafe_allow_html=True)

                r2c1, r2c2, r2c3 = st.columns(3)
                for col, lbl, val in [
                    (r2c1, "Trade-off Thinking", llm.trade_off_thinking),
                    (r2c2, "Answer Maturity",    llm.answer_maturity),
                    (r2c3, "Overall LLM Score",  llm.overall_llm_score),
                ]:
                    with col: st.markdown(_mcard(lbl, f"{val:.1f}/10", val/10), unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                for lbl, txt in [
                    ("Technical",  llm.technical_feedback),
                    ("Reasoning",  llm.reasoning_feedback),
                    ("Trade-offs", llm.trade_off_feedback),
                    ("Maturity",   llm.maturity_feedback),
                ]:
                    if txt:
                        st.markdown(f'<div class="fb-item"><strong>{lbl}:</strong> {txt}</div>', unsafe_allow_html=True)

                if llm.interviewer_summary:
                    st.markdown(f"""
                    <div class="note-cyan" style="margin-top:0.6rem;">
                      <p style="font-size:0.72rem;font-weight:600;color:#22D3EE;margin:0 0 0.2rem;">💼 Interviewer Notes</p>
                      <p style="font-size:0.82rem;color:#94A3B8;margin:0;">{llm.interviewer_summary}</p>
                    </div>""", unsafe_allow_html=True)

                if llm.follow_up_questions:
                    st.markdown('<p style="font-size:0.78rem;font-weight:600;color:#94A3B8;margin:0.75rem 0 0.3rem;">An interviewer might ask next:</p>', unsafe_allow_html=True)
                    for fq in llm.follow_up_questions:
                        st.markdown(f'<p style="font-size:0.8rem;color:#64748B;margin:0.1rem 0 0.1rem 0.75rem;">→ <em style="color:#6366F1;">{fq}</em></p>', unsafe_allow_html=True)

            # ── Rule-Based ─────────────────────────────────────────────────
            if ev.rule_based_score:
                rb = ev.rule_based_score
                st.markdown('<div class="sec-head"><span class="sec-head-icon">📊</span><p class="sec-head-title">Objective Rule-Based Metrics</p></div>', unsafe_allow_html=True)

                rc1, rc2, rc3, rc4, rc5 = st.columns(5)
                for col, lbl, val, mv in [
                    (rc1, "Ownership",      rb.ownership_score,      10),
                    (rc2, "Impact",         rb.impact_score,         10),
                    (rc3, "Skill Coverage", rb.skill_coverage_pct,  100),
                    (rc4, "STAR Structure", rb.star_structure_score, 10),
                    (rc5, "Completeness",   rb.word_count_score,     10),
                ]:
                    disp = f"{val:.0f}%" if mv == 100 else f"{val:.1f}"
                    with col: st.markdown(_mcard(lbl, disp, val/mv), unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                if rb.matched_skills:
                    st.markdown('<p style="font-size:0.75rem;font-weight:600;color:#94A3B8;margin-bottom:0.3rem;">✅ Skills mentioned</p>', unsafe_allow_html=True)
                    st.markdown("".join(f'<span class="pill pill-green">{s}</span>' for s in rb.matched_skills[:8]), unsafe_allow_html=True)
                if rb.missing_skills:
                    st.markdown('<p style="font-size:0.75rem;font-weight:600;color:#94A3B8;margin:0.5rem 0 0.3rem;">❌ Not mentioned</p>', unsafe_allow_html=True)
                    st.markdown("".join(f'<span class="pill pill-red">{s}</span>' for s in rb.missing_skills[:8]), unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                for fb in [rb.ownership_feedback, rb.impact_feedback, rb.skill_feedback,
                           rb.star_feedback, rb.completeness_feedback]:
                    if fb: st.markdown(f'<div class="fb-item">{fb}</div>', unsafe_allow_html=True)

            # ── Communication ──────────────────────────────────────────────
            comm = ev.communication
            st.markdown('<div class="sec-head"><span class="sec-head-icon">🗣️</span><p class="sec-head-title">Communication Analysis</p></div>', unsafe_allow_html=True)

            cc1, cc2, cc3, cc4 = st.columns(4)
            for col, lbl, val, mv in [
                (cc1, "Comm Score",   comm.score,           10),
                (cc2, "Reading Ease", comm.reading_ease,   100),
                (cc3, "Filler Words", float(comm.filler_word_count), None),
                (cc4, "Word Count",   float(comm.word_count),        None),
            ]:
                with col:
                    if mv:
                        st.markdown(_mcard(lbl, f"{val:.1f}", val/mv), unsafe_allow_html=True)
                    else:
                        if lbl == "Filler Words":
                            n2 = 1.0 if val == 0 else max(0, 1 - val/10)
                        else:
                            n2 = 1.0 if 80 <= val <= 200 else 0.5
                        st.markdown(_mcard(lbl, str(int(val)), n2), unsafe_allow_html=True)

            # STAR sub-scores
            star = ev.star_score
            if star.total > 0:
                st.markdown('<p style="font-size:0.75rem;font-weight:600;color:#94A3B8;margin:1rem 0 0.5rem;">STAR Method (LLM-assessed)</p>', unsafe_allow_html=True)
                ss1, ss2, ss3, ss4 = st.columns(4)
                for col, lbl, val in [(ss1,"Situation",star.situation_score),
                                      (ss2,"Task",     star.task_score),
                                      (ss3,"Action",   star.action_score),
                                      (ss4,"Result",   star.result_score)]:
                    with col: st.markdown(_mcard(lbl, f"{val:.1f}", val/10), unsafe_allow_html=True)

            # Final + tips
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);'
                f'border-radius:10px;padding:1rem 1.25rem;">'
                f'<p style="font-weight:700;font-size:0.95rem;color:{t_hex};margin:0 0 0.5rem;">'
                f'🏆 Final Score: {ev.composite_score:.0f}/100 — {tl}</p>',
                unsafe_allow_html=True)
            for tip in ev.improvement_tips:
                st.markdown(f'<div class="tip-item">💡 {tip}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Recommendations ────────────────────────────────────────────────────
    st.markdown('<hr style="border-color:rgba(255,255,255,0.07);margin:1.5rem 0;">', unsafe_allow_html=True)
    st.markdown('<p style="font-size:1rem;font-weight:700;color:#F1F5F9;margin-bottom:1rem;">🎯 Recommended Next Steps</p>', unsafe_allow_html=True)

    icons = ["📚", "🎙️", "📊", "🔍", "💬"]
    recs  = report.practice_recommendations
    cols  = st.columns(min(len(recs), 3), gap="small")
    for i, rec in enumerate(recs):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="glass" style="text-align:center;padding:1.25rem 1rem;">
              <div style="font-size:1.4rem;margin-bottom:0.5rem;">{icons[i % 5]}</div>
              <p style="font-size:0.8rem;color:#94A3B8;line-height:1.55;margin:0;">{rec}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    nc1, nc2, nc3 = st.columns([3, 2, 3])
    with nc2:
        if st.button("🔄 New Session", use_container_width=True, key="new_sess"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    init_state()
    step = st.session_state.step
    if   step == 0: render_landing()
    elif step == 1: render_step1()
    elif step == 2: render_step2()
    elif step == 3: render_step3()

main()
