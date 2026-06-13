"""
app.py — Module 3: Streamlit frontend for the AI Interview Readiness Analyzer.

Three-step flow:
  1. JD Setup       — paste a job description, generate role-specific questions
  2. Mock Interview — answer a chosen number of questions one at a time
  3. Readiness Report — composite score, STAR/relevance/communication breakdown,
                        strengths, gaps, and practice recommendations

Run with:
    venv\\Scripts\\python.exe -m streamlit run app.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from src.jd_parser import JDParser
from src.question_gen import QuestionGenerator
from src.evaluator import EvaluationEngine
from src.schemas import QAPair, ReadinessReport, QuestionType


# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────

st.set_page_config(
    page_title="AI Interview Readiness Analyzer",
    page_icon="🎯",
    layout="wide",
)


# ─────────────────────────────────────────
# CACHED RESOURCES
# Heavy objects (spaCy model, sentence-transformers, LLM clients) are
# created once per session and reused across reruns.
# ─────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_jd_parser():
    return JDParser()


@st.cache_resource(show_spinner=False)
def get_question_generator():
    return QuestionGenerator()


@st.cache_resource(show_spinner=False)
def get_evaluation_engine():
    return EvaluationEngine()


# ─────────────────────────────────────────
# SESSION STATE INITIALISATION
# ─────────────────────────────────────────

def init_state():
    defaults = {
        "step":            1,       # 1=JD setup, 2=interview, 3=report
        "parsed_jd":       None,
        "question_bank":   None,
        "num_questions":   3,
        "current_q_idx":   0,
        "qa_pairs":        [],      # list of QAPair as user answers
        "evaluations":     [],
        "report":          None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()


init_state()


# ─────────────────────────────────────────
# SAMPLE JD (for quick demo)
# ─────────────────────────────────────────

SAMPLE_JD = """Senior Backend Engineer

We are looking for a Senior Backend Engineer with 6+ years of experience
to join our growing platform team.

Requirements:
- Strong proficiency in Python and FastAPI
- Experience with PostgreSQL and Redis
- Familiarity with Docker and AWS
- Solid understanding of REST API design

Nice to have:
- Experience with Kafka
- Exposure to Kubernetes

Responsibilities:
- Design and build scalable backend services
- Collaborate with frontend and product teams
- Mentor junior engineers
- Participate in code reviews
"""


# ─────────────────────────────────────────
# SIDEBAR — progress + reset
# ─────────────────────────────────────────

with st.sidebar:
    st.title("🎯 Interview Readiness")
    st.caption("AI-powered mock interview & feedback")

    steps = ["1. Job Setup", "2. Mock Interview", "3. Readiness Report"]
    for i, label in enumerate(steps, start=1):
        if st.session_state.step == i:
            st.markdown(f"**➡️ {label}**")
        elif st.session_state.step > i:
            st.markdown(f"✅ {label}")
        else:
            st.markdown(f"⬜ {label}")

    st.divider()
    if st.button("🔄 Start Over", use_container_width=True):
        reset_all()
        st.rerun()

    if not os.getenv("GEMINI_API_KEY"):
        st.warning("GEMINI_API_KEY not found in .env — question generation and "
                    "evaluation will fail until it's set.")


# ═════════════════════════════════════════
# STEP 1 — JD SETUP
# ═════════════════════════════════════════

if st.session_state.step == 1:
    st.header("Step 1 — Paste the Job Description")
    st.write("Paste a real job description below. We'll extract the role, "
             "skills, and experience level, then generate tailored interview questions.")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Use sample JD", use_container_width=True):
            st.session_state["jd_text_input"] = SAMPLE_JD

    jd_text = st.text_area(
        "Job description",
        value=st.session_state.get("jd_text_input", ""),
        height=280,
        placeholder="Paste the full job description here...",
        key="jd_text_input",
    )

    st.session_state.num_questions = st.slider(
        "How many questions for this practice session?",
        min_value=1, max_value=10, value=st.session_state.num_questions,
        help="Each question requires a Gemini API call to evaluate your answer. "
             "Start with 3 for a quick demo.",
    )

    if st.button("Generate Interview Questions →", type="primary", disabled=not jd_text.strip()):
        with st.spinner("Parsing job description..."):
            parser = get_jd_parser()
            parsed_jd = parser.parse(jd_text)
            st.session_state.parsed_jd = parsed_jd

        with st.spinner("Generating tailored interview questions (calling Gemini)..."):
            try:
                qgen = get_question_generator()
                bank = qgen.generate(parsed_jd)
                st.session_state.question_bank = bank
                st.session_state.step = 2
                st.rerun()
            except Exception as e:
                st.error(f"Question generation failed: {e}")

    # Show parsed JD preview if already parsed
    if st.session_state.parsed_jd:
        with st.expander("Parsed job description details", expanded=False):
            jd = st.session_state.parsed_jd
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Role:** {jd.role_title}")
                st.markdown(f"**Experience level:** {jd.experience_level}")
                st.markdown(f"**Tech stack:** {', '.join(jd.tech_stack) or '—'}")
            with c2:
                st.markdown("**Required skills:**")
                for s in jd.required_skills[:6]:
                    st.markdown(f"- {s}")


# ═════════════════════════════════════════
# STEP 2 — MOCK INTERVIEW
# ═════════════════════════════════════════

elif st.session_state.step == 2:
    bank = st.session_state.question_bank
    questions = bank.questions[: st.session_state.num_questions]
    total = len(questions)
    idx = st.session_state.current_q_idx

    st.header(f"Step 2 — Mock Interview: {bank.role}")
    st.progress(idx / total, text=f"Question {min(idx + 1, total)} of {total}")

    if idx < total:
        q = questions[idx]

        type_colors = {
            QuestionType.BEHAVIOURAL: "🔵",
            QuestionType.TECHNICAL:   "🟢",
            QuestionType.SITUATIONAL: "🟡",
            QuestionType.CULTURE_FIT: "🟣",
        }
        st.markdown(
            f"{type_colors.get(q.type, '⚪')} **{q.type.value.replace('_', ' ').title()}** "
            f"· Difficulty: *{q.difficulty.value}*"
        )
        st.subheader(q.text)

        if q.star_applicable:
            st.caption("💡 Tip: structure your answer using STAR — Situation, Task, Action, Result.")

        answer = st.text_area(
            "Your answer",
            height=180,
            key=f"answer_{idx}",
            placeholder="Type your answer here...",
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if idx > 0:
                if st.button("← Previous question"):
                    st.session_state.current_q_idx -= 1
                    st.rerun()
        with col2:
            next_label = "Next question →" if idx < total - 1 else "Finish & Evaluate →"
            if st.button(next_label, type="primary", disabled=not answer.strip()):
                qa = QAPair(question=q, answer=answer.strip())
                # Replace if re-answering, else append
                if len(st.session_state.qa_pairs) > idx:
                    st.session_state.qa_pairs[idx] = qa
                else:
                    st.session_state.qa_pairs.append(qa)

                if idx < total - 1:
                    st.session_state.current_q_idx += 1
                    st.rerun()
                else:
                    st.session_state.step = 3
                    st.rerun()

    else:
        st.session_state.step = 3
        st.rerun()


# ═════════════════════════════════════════
# STEP 3 — READINESS REPORT
# ═════════════════════════════════════════

elif st.session_state.step == 3:
    st.header("Step 3 — Your Interview Readiness Report")

    if st.session_state.report is None:
        with st.spinner(f"Evaluating {len(st.session_state.qa_pairs)} answer(s) "
                         f"(STAR scoring, relevance, communication)..."):
            try:
                engine = get_evaluation_engine()
                evaluations = engine.evaluate_all(st.session_state.qa_pairs)
                st.session_state.evaluations = evaluations
                st.session_state.report = ReadinessReport.from_evaluations(
                    evaluations, st.session_state.parsed_jd
                )
            except Exception as e:
                st.error(f"Evaluation failed: {e}")
                st.stop()

    report = st.session_state.report

    # ── Overall score gauge ──────────────────────────
    col1, col2 = st.columns([1, 2])

    with col1:
        tier_colors = {"Excellent": "#2ECC71", "Good": "#F1C40F", "Needs Work": "#E74C3C"}
        color = tier_colors.get(report.overall_tier.value, "#3498DB")

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=report.overall_score,
            title={"text": f"Overall Readiness — {report.overall_tier.value}"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 50], "color": "#FADBD8"},
                    {"range": [50, 75], "color": "#FCF3CF"},
                    {"range": [75, 100], "color": "#D5F5E3"},
                ],
            },
        ))
        fig.update_layout(height=300, margin=dict(t=60, b=10, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Strengths")
        for s in report.top_strengths:
            st.success(f"✅ {s}")

        st.markdown("### Areas to improve")
        for g in report.top_gaps:
            st.warning(f"⚠️ {g}")

    st.divider()

    # ── Per-question breakdown ──────────────────────
    st.markdown("### Per-question breakdown")

    chart_data = {
        "Question": [f"Q{i+1}" for i in range(len(report.evaluations))],
        "Composite Score": [e.composite_score for e in report.evaluations],
    }
    bar_fig = px.bar(
        chart_data, x="Question", y="Composite Score",
        range_y=[0, 100], color="Composite Score",
        color_continuous_scale=["#E74C3C", "#F1C40F", "#2ECC71"],
        text="Composite Score",
    )
    bar_fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    bar_fig.update_layout(height=350, coloraxis_showscale=False)
    st.plotly_chart(bar_fig, use_container_width=True)

    for i, ev in enumerate(report.evaluations, start=1):
        with st.expander(f"Q{i}: {ev.qa_pair.question.text[:80]}... "
                          f"— Score: {ev.composite_score:.0f}/100 ({ev.tier.value})"):
            st.markdown(f"**Your answer:** {ev.qa_pair.answer}")
            st.markdown("---")

            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.metric("STAR total", f"{ev.star_score.total:.1f}/10")
                st.caption(f"Situation: {ev.star_score.situation_score:.1f} · "
                           f"Task: {ev.star_score.task_score:.1f}")
                st.caption(f"Action: {ev.star_score.action_score:.1f} · "
                           f"Result: {ev.star_score.result_score:.1f}")
            with sc2:
                st.metric("Content relevance", f"{ev.content_relevance * 100:.0f}%")
                if ev.flagged_off_topic:
                    st.caption("⚠️ Flagged as possibly off-topic")
            with sc3:
                st.metric("Communication", f"{ev.communication.score:.1f}/10")
                st.caption(f"Filler words: {ev.communication.filler_word_count} · "
                           f"Reading ease: {ev.communication.reading_ease:.0f}")

            st.markdown("**Improvement tips:**")
            for tip in ev.improvement_tips:
                st.markdown(f"- {tip}")

    st.divider()

    # ── Practice recommendations ─────────────────────
    st.markdown("### Recommended next steps")
    rec_lines = "\n".join(
        f"{i}. {rec}" for i, rec in enumerate(report.practice_recommendations, start=1)
    )
    st.markdown(rec_lines)

    st.divider()
    if st.button("🔄 Start a new practice session"):
        reset_all()
        st.rerun()
