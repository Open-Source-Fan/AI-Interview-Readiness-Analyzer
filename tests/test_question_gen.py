"""
test_question_gen.py — Unit tests for Module 2 (Question Generator).

These tests use a FAKE LLM (no real API calls) to test the parsing,
validation, and fallback logic in QuestionGenerator. This means they
run for free and don't need GEMINI_API_KEY.

A separate live test (test_question_gen_live) is skipped by default
and only runs if RUN_LIVE_TESTS=1 is set, for real end-to-end checks.
"""

import json
import os
import pytest

from src.question_gen import QuestionGenerator
from src.schemas import ParsedJD, QuestionBank, QuestionType


# ─────────────────────────────────────────
# FAKE LLM — mimics LangChain's .invoke() interface
# ─────────────────────────────────────────

from langchain_core.runnables import Runnable


class FakeResponse:
    def __init__(self, content: str):
        self.content = content


class FakeLLM(Runnable):
    """A drop-in fake for ChatGoogleGenerativeAI. Returns a fixed JSON string."""

    def __init__(self, response_text: str):
        self._response_text = response_text

    def invoke(self, _inputs, config=None, **kwargs):
        return FakeResponse(self._response_text)

VALID_QUESTIONS_JSON = json.dumps([
    {"id": "Q01", "text": "Tell me about a time you debugged a tricky issue.",
     "type": "behavioural", "difficulty": "medium", "star_applicable": True,
     "ideal_topics": ["debugging", "ownership"]},
    {"id": "Q02", "text": "Tell me about a time you led a project.",
     "type": "behavioural", "difficulty": "medium", "star_applicable": True,
     "ideal_topics": ["leadership"]},
    {"id": "Q03", "text": "Tell me about a conflict with a teammate.",
     "type": "behavioural", "difficulty": "easy", "star_applicable": True,
     "ideal_topics": ["conflict"]},
    {"id": "Q04", "text": "Tell me about a deadline you almost missed.",
     "type": "behavioural", "difficulty": "medium", "star_applicable": True,
     "ideal_topics": ["time management"]},
    {"id": "Q05", "text": "How would you design a REST API for a todo app?",
     "type": "technical", "difficulty": "medium", "star_applicable": False,
     "ideal_topics": ["API design"]},
    {"id": "Q06", "text": "What is the difference between SQL and NoSQL?",
     "type": "technical", "difficulty": "easy", "star_applicable": False,
     "ideal_topics": ["databases"]},
    {"id": "Q07", "text": "How do you optimise a slow database query?",
     "type": "technical", "difficulty": "hard", "star_applicable": False,
     "ideal_topics": ["performance"]},
    {"id": "Q08", "text": "How would you handle a production outage at 2am?",
     "type": "situational", "difficulty": "hard", "star_applicable": True,
     "ideal_topics": ["incident response"]},
    {"id": "Q09", "text": "How would you onboard a new teammate?",
     "type": "situational", "difficulty": "easy", "star_applicable": True,
     "ideal_topics": ["mentorship"]},
    {"id": "Q10", "text": "What kind of team culture helps you thrive?",
     "type": "culture_fit", "difficulty": "easy", "star_applicable": False,
     "ideal_topics": ["culture"]},
])


@pytest.fixture
def sample_jd():
    return ParsedJD(
        raw_text="Senior Python Backend Engineer with FastAPI and AWS experience.",
        role_title="Backend Engineer",
        experience_level="Senior",
        required_skills=["Python", "FastAPI"],
        nice_to_have=["Kafka"],
        tech_stack=["Python", "FastAPI", "AWS"],
        responsibilities=["Build APIs", "Mentor juniors"],
    )


# ── Happy path ─────────────────────────────────────────────

def test_generate_returns_question_bank(sample_jd):
    fake_llm = FakeLLM(VALID_QUESTIONS_JSON)
    gen = QuestionGenerator(llm=fake_llm)

    bank = gen.generate(sample_jd)

    assert isinstance(bank, QuestionBank)
    assert bank.role == "Backend Engineer"
    assert len(bank.questions) == 10

def test_question_type_distribution(sample_jd):
    fake_llm = FakeLLM(VALID_QUESTIONS_JSON)
    gen = QuestionGenerator(llm=fake_llm)

    bank = gen.generate(sample_jd)

    assert len(bank.by_type(QuestionType.BEHAVIOURAL)) == 4
    assert len(bank.by_type(QuestionType.TECHNICAL))   == 3
    assert len(bank.by_type(QuestionType.SITUATIONAL)) == 2
    assert len(bank.by_type(QuestionType.CULTURE_FIT)) == 1


# ── Markdown fence handling ───────────────────────────────

def test_handles_markdown_fences(sample_jd):
    wrapped = "```json\n" + VALID_QUESTIONS_JSON + "\n```"
    fake_llm = FakeLLM(wrapped)
    gen = QuestionGenerator(llm=fake_llm)

    bank = gen.generate(sample_jd)
    assert len(bank.questions) == 10


# ── Malformed response → fallback questions ──────────────

def test_malformed_json_uses_fallback(sample_jd):
    fake_llm = FakeLLM("This is not JSON at all, sorry!")
    gen = QuestionGenerator(llm=fake_llm)

    bank = gen.generate(sample_jd)

    # Should still produce a valid bank via fallback questions
    assert isinstance(bank, QuestionBank)
    assert len(bank.questions) >= 5

def test_empty_array_uses_fallback(sample_jd):
    fake_llm = FakeLLM("[]")
    gen = QuestionGenerator(llm=fake_llm)

    bank = gen.generate(sample_jd)
    assert len(bank.questions) >= 5


# ── Invalid field values get safe defaults ────────────────

def test_invalid_type_defaults_to_behavioural(sample_jd):
    bad_json = json.dumps([
        {"id": "Q01", "text": "Some question?", "type": "not_a_real_type",
         "difficulty": "medium", "star_applicable": True, "ideal_topics": []},
    ] * 5)  # repeat to satisfy minimum 5
    fake_llm = FakeLLM(bad_json)
    gen = QuestionGenerator(llm=fake_llm)

    bank = gen.generate(sample_jd)
    assert all(q.type == QuestionType.BEHAVIOURAL for q in bank.questions[:5])

def test_missing_text_gets_default(sample_jd):
    bad_json = json.dumps([
        {"id": "Q01", "type": "behavioural", "difficulty": "medium",
         "star_applicable": True, "ideal_topics": []},
    ] * 5)
    fake_llm = FakeLLM(bad_json)
    gen = QuestionGenerator(llm=fake_llm)

    bank = gen.generate(sample_jd)
    assert all(len(q.text) > 0 for q in bank.questions)


# ─────────────────────────────────────────
# LIVE TEST (real Gemini API call) — opt-in only
# ─────────────────────────────────────────

@pytest.mark.skipif(
    os.getenv("RUN_LIVE_TESTS") != "1",
    reason="Set RUN_LIVE_TESTS=1 and GEMINI_API_KEY to run real API tests",
)
def test_question_gen_live(sample_jd):
    """Real end-to-end test against Gemini. Costs a tiny amount / uses free tier."""
    gen = QuestionGenerator()  # uses GEMINI_API_KEY from env
    bank = gen.generate(sample_jd)

    assert isinstance(bank, QuestionBank)
    assert len(bank.questions) >= 5
    for q in bank.questions:
        assert len(q.text) > 5
