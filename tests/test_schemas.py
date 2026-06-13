"""
test_schemas.py — Unit tests for all Pydantic schemas.
Run: pytest tests/test_schemas.py -v
"""

import pytest
from pydantic import ValidationError
from src.schemas import (
    ParsedJD, Question, QuestionBank, QuestionType, Difficulty,
    QAPair, STARScore, CommunicationScore, ReadinessReport, ReadinessTier
)


# ── ParsedJD ──────────────────────────────────────────────

def test_parsed_jd_valid():
    jd = ParsedJD(
        raw_text="We need a Python engineer",
        role_title="Backend Engineer",
        experience_level="Mid",
        required_skills=["Python", "FastAPI"],
        tech_stack=["PostgreSQL", "Docker"],
        responsibilities=["Build APIs", "Write tests"],
    )
    assert jd.role_title == "Backend Engineer"

def test_parsed_jd_empty_title_fails():
    with pytest.raises(ValidationError):
        ParsedJD(raw_text="text", role_title="   ", experience_level="Mid")

def test_parsed_jd_title_stripped():
    jd = ParsedJD(raw_text="text", role_title="  SWE  ", experience_level="Senior")
    assert jd.role_title == "SWE"


# ── QuestionBank ──────────────────────────────────────────

def _make_question(qid: str, qtype: QuestionType) -> Question:
    return Question(
        id=qid, text=f"Question {qid}",
        type=qtype, difficulty=Difficulty.MEDIUM,
        star_applicable=True, ideal_topics=["a", "b"],
    )

def test_question_bank_valid():
    qs = [_make_question(f"Q0{i}", QuestionType.BEHAVIOURAL) for i in range(5)]
    bank = QuestionBank(role="SWE", questions=qs)
    assert len(bank.questions) == 5

def test_question_bank_too_few_questions():
    qs = [_make_question("Q01", QuestionType.BEHAVIOURAL)]
    with pytest.raises(ValidationError):
        QuestionBank(role="SWE", questions=qs)

def test_question_bank_by_type():
    qs = [
        _make_question("Q01", QuestionType.BEHAVIOURAL),
        _make_question("Q02", QuestionType.TECHNICAL),
        _make_question("Q03", QuestionType.BEHAVIOURAL),
        _make_question("Q04", QuestionType.SITUATIONAL),
        _make_question("Q05", QuestionType.CULTURE_FIT),
    ]
    bank = QuestionBank(role="PM", questions=qs)
    assert len(bank.by_type(QuestionType.BEHAVIOURAL)) == 2
    assert len(bank.by_type(QuestionType.TECHNICAL))   == 1


# ── QAPair ────────────────────────────────────────────────

def test_qa_pair_empty_answer_fails():
    q = _make_question("Q01", QuestionType.BEHAVIOURAL)
    with pytest.raises(ValidationError):
        QAPair(question=q, answer="   ")


# ── STARScore ─────────────────────────────────────────────

def test_star_score_total():
    s = STARScore(
        situation_score=8, task_score=7, action_score=9, result_score=6,
        situation_evidence="we had a deadline",
        task_evidence="my job was to fix it",
        action_evidence="I refactored the module",
        result_evidence="reduced errors by 40%",
    )
    assert s.total == 7.5

def test_star_missing_components():
    s = STARScore(
        situation_score=2, task_score=2, action_score=8, result_score=9,
        situation_evidence="not mentioned",
        task_evidence="not mentioned",
        action_evidence="I rewrote it",
        result_evidence="saved 2 hours daily",
    )
    assert "Situation" in s.missing_components
    assert "Task"      in s.missing_components
    assert "Action"    not in s.missing_components


# ── CommunicationScore ────────────────────────────────────

def test_communication_score_range():
    c = CommunicationScore(
        reading_ease=65, avg_sentence_len=14, filler_word_count=0,
        passive_voice_pct=10, vocabulary_diversity=0.7, word_count=120,
    )
    assert 0 <= c.score <= 10

def test_high_filler_penalises_score():
    low  = CommunicationScore(reading_ease=65, avg_sentence_len=14, filler_word_count=0,  passive_voice_pct=10, vocabulary_diversity=0.6, word_count=100)
    high = CommunicationScore(reading_ease=65, avg_sentence_len=14, filler_word_count=10, passive_voice_pct=10, vocabulary_diversity=0.6, word_count=100)
    assert low.score > high.score


# ── ReadinessReport factory ───────────────────────────────

def _make_full_evaluation(composite_override: float | None = None):
    from src.schemas import QuestionEvaluation
    q      = _make_question("Q01", QuestionType.BEHAVIOURAL)
    pair   = QAPair(question=q, answer="I led a project that saved 30% costs.")
    star   = STARScore(
        situation_score=8, task_score=7, action_score=8, result_score=9,
        situation_evidence="led a project",
        task_evidence="my responsibility",
        action_evidence="I restructured the team",
        result_evidence="saved 30% costs",
    )
    comm = CommunicationScore(
        reading_ease=70, avg_sentence_len=12, filler_word_count=0,
        passive_voice_pct=5, vocabulary_diversity=0.65, word_count=80,
    )
    return QuestionEvaluation(
        qa_pair=pair, star_score=star,
        content_relevance=0.85, communication=comm,
        improvement_tips=["Quantify the result more.", "Add the exact timeframe."],
    )

def test_report_from_evaluations():
    evals = [_make_full_evaluation()]
    jd    = ParsedJD(raw_text="text", role_title="SWE", experience_level="Mid")
    report = ReadinessReport.from_evaluations(evals, jd, candidate_name="Test User")
    assert report.overall_score > 0
    assert report.overall_tier in list(ReadinessTier)
    assert 1 <= len(report.top_strengths) <= 3
    assert 1 <= len(report.top_gaps) <= 3
    assert 3 <= len(report.practice_recommendations) <= 5

def test_report_low_scores_produce_gaps():
    """A low-scoring evaluation should surface gaps, not just strengths."""
    from src.schemas import QuestionEvaluation
    q    = _make_question("Q01", QuestionType.BEHAVIOURAL)
    pair = QAPair(question=q, answer="I don't really remember, it was fine I guess.")
    star = STARScore(
        situation_score=1, task_score=1, action_score=2, result_score=1,
        situation_evidence="not mentioned",
        task_evidence="not mentioned",
        action_evidence="not mentioned",
        result_evidence="not mentioned",
    )
    comm = CommunicationScore(
        reading_ease=40, avg_sentence_len=8, filler_word_count=6,
        passive_voice_pct=30, vocabulary_diversity=0.3, word_count=20,
    )
    low_eval = QuestionEvaluation(
        qa_pair=pair, star_score=star,
        content_relevance=0.2, communication=comm,
        improvement_tips=["Add a specific situation.", "Quantify the result."],
    )

    jd = ParsedJD(raw_text="text", role_title="SWE", experience_level="Mid")
    report = ReadinessReport.from_evaluations([low_eval], jd)

    assert report.overall_tier == ReadinessTier.NEEDS_WORK
    assert 1 <= len(report.top_gaps) <= 3
    assert 1 <= len(report.top_strengths) <= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
