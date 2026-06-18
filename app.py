"""
app.py — Streamlit Frontend for AI Interview Readiness Analyzer
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

st.set_page_config(
    page_title="AI Interview Readiness Analyzer",
    page_icon="🎯",
    layout="wide",
)

st.markdown("""
<style>
    .stApp, p, li, div, span { font-size: 1rem !important; }
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.6rem !important; }
    h3 { font-size: 1.25rem !important; }
    .stButton > button { font-size: 1rem !important; padding: 0.5rem 1.2rem !important; }
    .stTextArea textarea { font-size: 1rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem !important; }
</style>
""", unsafe_allow_html=True)

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
        "step": 1,
        "parsed_jd": None,
        "question_bank": None,
        "current_q_idx": 0,
        "answers": {},
        "qa_pairs": [],
        "report": None,
        "jd_text": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎯 Interview Readiness")
        st.markdown("AI-powered mock interview & feedback")
        st.divider()
        for num, label in [(1,"1. Job Setup"),(2,"2. Mock Interview"),(3,"3. Readiness Report")]:
            if num == st.session_state.step:
                st.markdown(f"**➡️ {label}**")
            elif num < st.session_state.step:
                st.markdown(f"✅ {label}")
            else:
                st.markdown(f"⬜ {label}")
        if st.session_state.step > 1:
            st.divider()
            if st.button("🔄 Start Over", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()

# ── Step 1 ────────────────────────────────────────────────────────────────────

def render_step1():
    st.header("Step 1 — Paste the Job Description")
    st.markdown(
        "Paste a real job description below. We'll extract the role, skills, "
        "and experience level, then generate tailored interview questions."
    )

    # Sample JD button — writes to both backing state AND the widget key
    col_btn, col_spacer = st.columns([2, 5])
    with col_btn:
        if st.button("📋 Use sample JD", key="sample_jd_btn"):
            st.session_state.jd_text = SAMPLE_JD
            st.session_state.jd_textarea_main = SAMPLE_JD

    # text_area reads from session state — this always shows the current value
    # including after "Use sample JD" sets it above (same render cycle)
    jd_text = st.text_area(
        "Job description",
        value=st.session_state.jd_text,
        height=260,
        placeholder="Paste a job description here...",
        key="jd_textarea_main",
    )
    # Keep session state up to date as user types
    st.session_state.jd_text = jd_text

    n_questions = st.slider(
        "How many questions for this practice session?",
        min_value=1, max_value=10, value=3,
    )

    st.markdown("---")

    if st.button("🚀 Generate Questions", type="primary", use_container_width=True):
        text = st.session_state.jd_text.strip()
        if len(text) < 20:
            st.error("Please paste a real job description (at least 20 characters).")
            return

        with st.spinner("Parsing job description..."):
            parser = get_jd_parser()
            parsed_jd = parser.parse(text)
            st.session_state.parsed_jd = parsed_jd

        ca, cb, cc = st.columns(3)
        ca.metric("Role", parsed_jd.role_title)
        cb.metric("Level", parsed_jd.experience_level)
        cc.metric("Skills found", len(parsed_jd.required_skills) + len(parsed_jd.tech_stack))

        with st.spinner("Generating role-specific questions via Gemini..."):
            gen = get_question_generator()
            bank = gen.generate(parsed_jd)
            bank.questions = bank.questions[:n_questions]
            st.session_state.question_bank = bank

        st.success(f"✅ Generated {len(bank.questions)} questions for {parsed_jd.role_title}.")
        st.session_state.step = 2
        st.session_state.current_q_idx = 0
        st.session_state.answers = {}
        st.session_state.report = None
        st.rerun()

# ── Step 2 ────────────────────────────────────────────────────────────────────

def render_step2():
    bank = st.session_state.question_bank
    total = len(bank.questions)
    idx = st.session_state.current_q_idx

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

    st.header(f"Step 2 — Question {idx + 1} of {total}")
    st.progress(idx / total)

    badge = {
        "behavioural": "🟦 Behavioural",
        "technical":   "🟥 Technical",
        "situational": "🟨 Situational",
        "culture_fit": "🟩 Culture Fit",
    }.get(q.type.value, "⬜ General")

    st.markdown(f"**{badge}** &nbsp;·&nbsp; Difficulty: `{q.difficulty}`")
    st.divider()
    st.markdown(f"### {q.text}")

    if q.star_applicable:
        with st.expander("💡 STAR tip", expanded=False):
            st.markdown(
                "**S**ituation — set the context  \n"
                "**T**ask — what was your goal  \n"
                "**A**ction — what YOU specifically did ('I', not 'we')  \n"
                "**R**esult — measurable outcome"
            )

    answer = st.text_area(
        "Your answer",
        value=st.session_state.answers.get(idx, ""),
        height=200,
        placeholder="Type your answer here...",
        key=f"answer_q{idx}",
    )
    st.session_state.answers[idx] = answer

    st.divider()
    c1, c2, c3 = st.columns([1, 5, 1])
    with c1:
        if idx > 0 and st.button("← Back", key=f"back_{idx}"):
            st.session_state.current_q_idx -= 1
            st.rerun()
    with c3:
        label = "Finish ✓" if idx == total - 1 else "Next →"
        if st.button(label, type="primary", key=f"next_{idx}"):
            if not answer.strip():
                st.warning("Please type an answer before continuing.")
            else:
                st.session_state.current_q_idx += 1
                st.rerun()

# ── Step 3 ────────────────────────────────────────────────────────────────────

def _tier(score: float) -> str:
    if score >= 75: return "Excellent ✅"
    if score >= 50: return "Good 🟡"
    return "Needs Work 🔴"

def render_step3():
    st.header("Step 3 — Your Interview Readiness Report")

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

        with st.status("🤖 Evaluating your answers...", expanded=True) as status:
            st.write("Running AI Interviewer Assessment (Gemini)...")
            st.write("Scoring rule-based signals (ownership, impact, skills)...")
            st.write("Analysing communication quality (spaCy)...")
            engine = get_evaluation_engine()
            evaluations = engine.evaluate_all(qa_pairs, parsed_jd=parsed_jd)
            report = ReadinessReport.from_evaluations(evaluations, parsed_jd)
            st.session_state.report = report
            status.update(label="✅ Evaluation complete!", state="complete")

    report: ReadinessReport = st.session_state.report

    # Overall gauge
    colour = {"Excellent": "green", "Good": "orange", "Needs Work": "red"}.get(
        report.overall_tier.value, "gray"
    )
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=report.overall_score,
        title={"text": f"Overall Score — {report.overall_tier.value}", "font": {"size": 18}},
        number={"font": {"size": 40}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": colour},
            "steps": [
                {"range": [0,  50], "color": "#fee2e2"},
                {"range": [50, 75], "color": "#fef3c7"},
                {"range": [75,100], "color": "#d1fae5"},
            ],
        },
    ))
    fig.update_layout(height=260, margin=dict(t=60, b=10, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

    cs, cg = st.columns(2)
    with cs:
        st.markdown("#### ✅ Strengths")
        for s in report.top_strengths:
            st.success(s)
    with cg:
        st.markdown("#### ⚠️ Areas to Improve")
        for g in report.top_gaps:
            st.warning(g)

    st.divider()
    st.markdown("## 📋 Per-Question Breakdown")

    for i, ev in enumerate(report.evaluations):
        qtxt = ev.qa_pair.question.text
        qlabel = qtxt[:65] + ("..." if len(qtxt) > 65 else "")
        slabel = f"{ev.composite_score:.0f}/100 ({_tier(ev.composite_score)})"

        with st.expander(f"Q{i+1}: {qlabel} — {slabel}", expanded=(i == 0)):
            st.markdown(f"**Your answer:** {ev.qa_pair.answer[:300]}{'...' if len(ev.qa_pair.answer) > 300 else ''}")
            st.divider()

            # 1. AI Interviewer
            if ev.llm_eval_score is not None:
                st.markdown("### 🤖 AI Interviewer Assessment")
                llm = ev.llm_eval_score
                c1,c2,c3 = st.columns(3)
                c1.metric("Technical Depth",    f"{llm.technical_depth:.1f}/10")
                c2.metric("Reasoning Quality",  f"{llm.reasoning_quality:.1f}/10")
                c3.metric("Problem Solving",    f"{llm.problem_solving:.1f}/10")
                c4,c5,c6 = st.columns(3)
                c4.metric("Trade-off Thinking", f"{llm.trade_off_thinking:.1f}/10")
                c5.metric("Answer Maturity",    f"{llm.answer_maturity:.1f}/10")
                c6.metric("Overall LLM",        f"{llm.overall_llm_score:.1f}/10")
                for lbl, txt in [
                    ("Technical",  llm.technical_feedback),
                    ("Reasoning",  llm.reasoning_feedback),
                    ("Trade-offs", llm.trade_off_feedback),
                    ("Maturity",   llm.maturity_feedback),
                ]:
                    if txt:
                        st.markdown(f"**{lbl}:** {txt}")
                if llm.interviewer_summary:
                    st.info(f"💼 **Interviewer notes:** {llm.interviewer_summary}")
                if llm.follow_up_questions:
                    st.markdown("**An interviewer might ask:**")
                    for fq in llm.follow_up_questions:
                        st.markdown(f"- _{fq}_")
                st.divider()

            # 2. Objective Metrics
            if ev.rule_based_score is not None:
                st.markdown("### 📊 Objective Metrics")
                rb = ev.rule_based_score
                c1,c2,c3 = st.columns(3)
                c1.metric("Ownership",     f"{rb.ownership_score:.1f}/10")
                c2.metric("Impact",        f"{rb.impact_score:.1f}/10")
                c3.metric("Skill Coverage",f"{rb.skill_coverage_pct:.0f}%")
                c4,c5 = st.columns(2)
                c4.metric("STAR Structure",f"{rb.star_structure_score:.1f}/10")
                c5.metric("Answer Length", f"{rb.word_count_score:.1f}/10")
                if rb.ownership_signals:
                    st.markdown(f"✅ **Ownership signals:** {', '.join(rb.ownership_signals[:5])}")
                if rb.ownership_feedback:
                    st.caption(rb.ownership_feedback)
                if rb.impact_evidence:
                    st.markdown(f"📈 **Impact evidence:** {' | '.join(rb.impact_evidence[:3])}")
                if rb.impact_feedback:
                    st.caption(rb.impact_feedback)
                if rb.matched_skills:
                    st.markdown(f"🎯 **Skills matched:** {', '.join(rb.matched_skills[:6])}")
                if rb.missing_skills:
                    st.markdown(f"❌ **Not mentioned:** {', '.join(rb.missing_skills[:5])}")
                if rb.skill_feedback:
                    st.caption(rb.skill_feedback)
                if rb.star_feedback:
                    st.caption(rb.star_feedback)
                if rb.completeness_feedback:
                    st.caption(rb.completeness_feedback)
                st.divider()

            # 3. Communication
            st.markdown("### 🗣️ Communication Analysis")
            comm = ev.communication
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Comm Score",   f"{comm.score:.1f}/10")
            c2.metric("Reading Ease", f"{comm.reading_ease:.0f}/100")
            c3.metric("Filler Words", comm.filler_word_count)
            c4.metric("Word Count",   comm.word_count)
            star = ev.star_score
            if star.total > 0:
                st.markdown("**STAR scores (LLM-assessed):**")
                s1,s2,s3,s4 = st.columns(4)
                s1.metric("Situation", f"{star.situation_score:.1f}")
                s2.metric("Task",      f"{star.task_score:.1f}")
                s3.metric("Action",    f"{star.action_score:.1f}")
                s4.metric("Result",    f"{star.result_score:.1f}")
            st.divider()

            # 4. Final score
            st.markdown(
                f"### 🏆 Final Score: **{ev.composite_score:.0f}/100** — {_tier(ev.composite_score)}"
            )
            if ev.improvement_tips:
                st.markdown("**Improvement tips:**")
                for tip in ev.improvement_tips:
                    st.markdown(f"- {tip}")

    st.divider()
    st.markdown("## 🎯 Recommended Next Steps")
    for i, rec in enumerate(report.practice_recommendations, 1):
        st.markdown(f"{i}. {rec}")

    st.divider()
    st.info("📥 **Save this report:** Browser → Print → Save as PDF")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    init_state()
    render_sidebar()
    step = st.session_state.step
    if step == 1:
        render_step1()
    elif step == 2:
        render_step2()
    elif step == 3:
        render_step3()

main()
