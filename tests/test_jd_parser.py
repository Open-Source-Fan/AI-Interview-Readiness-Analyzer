"""
test_jd_parser.py — Unit tests for Module 1 (JD Parser).
No API calls — pure spaCy, runs fast and free.
"""

import pytest
from src.jd_parser import JDParser
from src.schemas import ParsedJD


SAMPLE_JD = """
Senior Backend Engineer

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

JUNIOR_JD = """
Job Title: Junior Data Analyst

We're hiring a Junior Data Analyst, entry-level, to join our analytics team.
You will work with SQL and Excel daily.

Requirements:
- SQL
- Excel
- Basic Python
"""


@pytest.fixture
def parser():
    return JDParser()


# ── Basic parsing ─────────────────────────────────────────

def test_parse_returns_parsed_jd(parser):
    result = parser.parse(SAMPLE_JD)
    assert isinstance(result, ParsedJD)

def test_empty_jd_raises(parser):
    with pytest.raises(ValueError):
        parser.parse("")
    with pytest.raises(ValueError):
        parser.parse("   ")


# ── Role title extraction ─────────────────────────────────

def test_role_title_senior(parser):
    result = parser.parse(SAMPLE_JD)
    assert "backend engineer" in result.role_title.lower()

def test_role_title_from_job_title_field(parser):
    result = parser.parse(JUNIOR_JD)
    assert "data analyst" in result.role_title.lower()


# ── Experience level extraction ───────────────────────────

def test_experience_level_senior(parser):
    result = parser.parse(SAMPLE_JD)
    assert result.experience_level == "Senior"

def test_experience_level_junior(parser):
    result = parser.parse(JUNIOR_JD)
    assert result.experience_level == "Junior"

def test_experience_level_default_mid(parser):
    jd = "We need someone great to join our team and do good work."
    result = parser.parse(jd)
    assert result.experience_level == "Mid"


# ── Tech stack extraction ─────────────────────────────────

def test_tech_stack_detected(parser):
    result = parser.parse(SAMPLE_JD)
    tech_lower = [t.lower() for t in result.tech_stack]
    assert "python" in tech_lower
    assert "fastapi" in tech_lower
    assert "postgresql" in tech_lower
    assert "docker" in tech_lower
    assert "aws" in tech_lower

def test_tech_stack_word_boundary(parser):
    """'Go' should not match inside words like 'Going' or 'Goal'."""
    jd = "We are going to achieve our goals together as a team."
    result = parser.parse(jd)
    assert "Go" not in result.tech_stack
    assert "GOLANG" not in result.tech_stack


# ── Required skills extraction ────────────────────────────

def test_required_skills_extracted(parser):
    result = parser.parse(SAMPLE_JD)
    assert len(result.required_skills) > 0
    joined = " ".join(result.required_skills).lower()
    assert "python" in joined or "fastapi" in joined

def test_required_skills_fallback_to_tech_stack(parser):
    """If no explicit requirements section exists, fall back to detected tech."""
    jd = "We use Python, Docker, and AWS extensively across our stack."
    result = parser.parse(jd)
    assert len(result.required_skills) > 0


# ── Nice-to-have extraction ────────────────────────────────

def test_nice_to_have_extracted(parser):
    result = parser.parse(SAMPLE_JD)
    joined = " ".join(result.nice_to_have).lower()
    assert "kafka" in joined or "kubernetes" in joined


# ── Responsibilities extraction ───────────────────────────

def test_responsibilities_extracted(parser):
    result = parser.parse(SAMPLE_JD)
    assert len(result.responsibilities) > 0
    joined = " ".join(result.responsibilities).lower()
    assert "design" in joined or "mentor" in joined or "collaborate" in joined


# ── Edge cases ─────────────────────────────────────────────

def test_minimal_jd_does_not_crash(parser):
    """A very short/vague JD should still return a valid ParsedJD."""
    result = parser.parse("Hiring a developer.")
    assert isinstance(result, ParsedJD)
    assert result.role_title  # not empty
    assert result.experience_level in ("Junior", "Mid", "Senior")
