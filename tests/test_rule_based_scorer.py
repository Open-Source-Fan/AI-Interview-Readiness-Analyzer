"""
test_rule_based_scorer.py — Unit tests for RuleBasedScorer.

All tests run in < 1 second with zero API calls.
Run: pytest tests/test_rule_based_scorer.py -v
"""

import pytest
from src.schemas import ParsedJD, Question, QuestionType
from src.rule_based_scorer import RuleBasedScorer


scorer = RuleBasedScorer()


def _make_question(ideal_topics: list[str] | None = None) -> Question:
    return Question(
        id="Q01",
        text="Tell me about a time you solved a hard production problem.",
        type=QuestionType.BEHAVIOURAL,
        ideal_topics=ideal_topics or [],
    )


def _make_jd(required_skills: list[str] = None, tech_stack: list[str] = None) -> ParsedJD:
    return ParsedJD(
        raw_text="We need a backend engineer.",
        role_title="Backend Engineer",
        required_skills=required_skills or [],
        tech_stack=tech_stack or [],
    )


# ── Ownership tests ────────────────────────────────────────────────────────────

def test_ownership_strong_answer():
    answer = "I designed the caching layer and implemented it using Redis. I led the migration and I deployed it to production."
    result = scorer._score_ownership(answer)
    assert result["score"] >= 6.0, f"Expected ≥6.0, got {result['score']}"
    assert len(result["signals"]) >= 2


def test_ownership_weak_answer():
    answer = "The team handled the migration. They decided to use Redis and it was set up by someone else."
    result = scorer._score_ownership(answer)
    assert result["score"] <= 3.0, f"Expected ≤3.0, got {result['score']}"


def test_ownership_feedback_present():
    answer = "I built the API."
    result = scorer._score_ownership(answer)
    assert isinstance(result["feedback"], str)
    assert len(result["feedback"]) > 10


# ── Impact / quantification tests ─────────────────────────────────────────────

def test_impact_with_percentages():
    answer = "I reduced latency by 40% and increased throughput by 3x."
    result = scorer._score_impact(answer)
    assert result["score"] >= 5.0


def test_impact_with_no_numbers():
    answer = "The performance improved significantly and users were happier."
    result = scorer._score_impact(answer)
    assert result["score"] == 0.0


def test_impact_evidence_collected():
    answer = "We saved $50k per month and reduced error rate from 5% to 0.1%."
    result = scorer._score_impact(answer)
    assert len(result["evidence"]) >= 1


# ── Skill coverage tests ───────────────────────────────────────────────────────

def test_skill_coverage_full_match():
    answer = "I used Python and FastAPI with PostgreSQL for the backend service."
    jd = _make_jd(required_skills=["python", "fastapi"], tech_stack=["postgresql"])
    q = _make_question()
    result = scorer._score_skill_coverage(answer, q, jd)
    assert result["coverage_pct"] >= 66.0  # at least 2/3 matched


def test_skill_coverage_no_match():
    answer = "I solved the problem by thinking carefully and working as a team."
    jd = _make_jd(required_skills=["kubernetes", "golang", "terraform"])
    q = _make_question()
    result = scorer._score_skill_coverage(answer, q, jd)
    assert result["coverage_pct"] == 0.0


def test_skill_coverage_neutral_when_no_jd():
    answer = "I built the feature using Python."
    q = _make_question()
    result = scorer._score_skill_coverage(answer, q, None)
    assert result["coverage_pct"] == 50.0  # neutral


def test_skill_coverage_uses_ideal_topics():
    answer = "I focused on debugging and system design in my approach."
    q = _make_question(ideal_topics=["debugging", "system design"])
    result = scorer._score_skill_coverage(answer, q, None)
    assert result["coverage_pct"] > 0


# ── STAR structure tests ───────────────────────────────────────────────────────

def test_star_structure_complete_answer():
    answer = (
        "At the time, we were handling 10k RPS and our service was degrading. "
        "My goal was to reduce p99 latency below 200ms. "
        "I profiled the hot path and found an N+1 query. I rewrote the data layer. "
        "As a result, latency dropped from 800ms to 120ms."
    )
    result = scorer._score_star_structure(answer)
    assert result["score"] >= 7.5


def test_star_structure_minimal_answer():
    answer = "I fixed the bug by rewriting the function."
    result = scorer._score_star_structure(answer)
    assert result["score"] <= 5.0


# ── Word count tests ───────────────────────────────────────────────────────────

def test_word_count_ideal_length():
    answer = " ".join(["word"] * 120)  # 120 words — ideal
    from src.rule_based_scorer import _word_count_score
    score, _ = _word_count_score(120)
    assert score == 10.0


def test_word_count_too_short():
    from src.rule_based_scorer import _word_count_score
    score, feedback = _word_count_score(15)
    assert score <= 2.0
    assert "short" in feedback.lower()


def test_word_count_too_long():
    from src.rule_based_scorer import _word_count_score
    score, feedback = _word_count_score(400)
    assert score <= 5.0


# ── Full scorer integration test ───────────────────────────────────────────────

def test_full_scorer_returns_rule_based_score():
    from src.schemas import RuleBasedScore
    answer = "I designed the system and reduced latency by 50%. I led the team of 3 engineers."
    q = _make_question(ideal_topics=["system design", "leadership"])
    jd = _make_jd(required_skills=["python"], tech_stack=["aws"])
    result = scorer.score(answer=answer, question=q, parsed_jd=jd)
    assert isinstance(result, RuleBasedScore)
    assert 0.0 <= result.ownership_score <= 10.0
    assert 0.0 <= result.impact_score <= 10.0
    assert 0.0 <= result.skill_coverage_pct <= 100.0
    assert 0.0 <= result.star_structure_score <= 10.0
    assert 0.0 <= result.word_count_score <= 10.0
    assert 0.0 <= result.composite <= 10.0
