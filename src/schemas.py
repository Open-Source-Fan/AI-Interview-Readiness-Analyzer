"""
schemas.py — Pydantic data models for the full evaluation pipeline.

All new fields on QuestionEvaluation are Optional with defaults so existing
tests continue to pass without any changes.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class QuestionType(str, Enum):
    BEHAVIOURAL  = "behavioural"
    TECHNICAL    = "technical"
    SITUATIONAL  = "situational"
    CULTURE_FIT  = "culture_fit"


class ReadinessTier(str, Enum):
    EXCELLENT  = "Excellent"
    GOOD       = "Good"
    NEEDS_WORK = "Needs Work"


# Kept for backward compatibility — question_gen.py imports this
class Difficulty(str, Enum):
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"


class ExperienceLevel(str, Enum):
    JUNIOR = "Junior"
    MID    = "Mid"
    SENIOR = "Senior"
    ANY    = "Any"


# ── JD & Question models ───────────────────────────────────────────────────────

class ParsedJD(BaseModel):
    raw_text:         str
    role_title:       str
    experience_level: str                  = ExperienceLevel.ANY
    required_skills:  list[str]            = []
    nice_to_have:     list[str]            = []
    tech_stack:       list[str]            = []
    responsibilities: list[str]            = []

    @field_validator("role_title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("role_title must not be empty")
        return v


class Question(BaseModel):
    id:             str
    text:           str
    type:           QuestionType           = QuestionType.BEHAVIOURAL
    difficulty:     str                    = "medium"
    star_applicable: bool                  = True
    ideal_topics:   list[str]             = []


class QuestionBank(BaseModel):
    role:      str
    questions: list[Question]

    @field_validator("questions")
    @classmethod
    def at_least_one(cls, v: list[Question]) -> list[Question]:
        if len(v) < 1:
            raise ValueError("QuestionBank must have at least 1 question")
        return v

    def by_type(self, qtype: QuestionType) -> list[Question]:
        return [q for q in self.questions if q.type == qtype]


class QAPair(BaseModel):
    question: Question
    answer:   str

    @field_validator("answer")
    @classmethod
    def answer_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("answer must not be empty")
        return v


# ── Sub-evaluation models ──────────────────────────────────────────────────────

class STARScore(BaseModel):
    situation_score:    float = 0.0
    task_score:         float = 0.0
    action_score:       float = 0.0
    result_score:       float = 0.0
    situation_evidence: str   = "not mentioned"
    task_evidence:      str   = "not mentioned"
    action_evidence:    str   = "not mentioned"
    result_evidence:    str   = "not mentioned"

    @property
    def total(self) -> float:
        return round(
            (self.situation_score + self.task_score +
             self.action_score + self.result_score) / 4,
            1,
        )

    @property
    def missing_components(self) -> list[str]:
        mapping = {
            "Situation": self.situation_score,
            "Task":      self.task_score,
            "Action":    self.action_score,
            "Result":    self.result_score,
        }
        return [k for k, v in mapping.items() if v < 3.0]


class CommunicationScore(BaseModel):
    reading_ease:       float = 0.0    # Flesch reading ease (0–100)
    avg_sentence_len:   float = 0.0
    filler_word_count:  int   = 0
    passive_voice_ratio: float = 0.0
    vocabulary_diversity: float = 0.0  # type/token ratio
    word_count:         int   = 0

    @property
    def score(self) -> float:
        """
        Heuristic 0–10 communication score.
        Penalises fillers and very long sentences; rewards reading ease.
        """
        base     = min(self.reading_ease / 10, 10.0)
        filler_p = min(self.filler_word_count * 0.5, 3.0)
        length_p = max(0.0, (self.avg_sentence_len - 25) * 0.1)
        return round(max(0.0, base - filler_p - length_p), 1)


# ── NEW: Rule-based score ──────────────────────────────────────────────────────

class RuleBasedScore(BaseModel):
    """
    Objective, explainable scores computed from the raw answer text using
    regex and keyword matching — no API call, runs in milliseconds.
    """
    # Ownership
    ownership_score:      float      = 0.0    # 0–10
    ownership_signals:    list[str]  = []     # matched phrases
    ownership_feedback:   str        = ""

    # Quantified impact
    impact_score:         float      = 0.0    # 0–10
    impact_evidence:      list[str]  = []     # "40%", "3x faster"
    impact_feedback:      str        = ""

    # Skill/keyword coverage vs JD
    skill_coverage_pct:   float      = 0.0    # 0–100
    matched_skills:       list[str]  = []
    missing_skills:       list[str]  = []
    skill_feedback:       str        = ""

    # STAR structure (rule-based heuristic, not LLM)
    star_structure_score: float      = 0.0    # 0–10
    star_hints_found:     list[str]  = []     # "past-tense+I", "result phrase"
    star_feedback:        str        = ""

    # Answer completeness
    word_count_score:     float      = 0.0    # 0–10
    word_count:           int        = 0
    completeness_feedback: str       = ""

    @property
    def composite(self) -> float:
        """Weighted composite 0–10 from the five sub-scores."""
        return round(
            self.ownership_score      * 0.25 +
            self.impact_score         * 0.25 +
            (self.skill_coverage_pct / 10) * 0.25 +
            self.star_structure_score * 0.15 +
            self.word_count_score     * 0.10,
            1,
        )


# ── NEW: LLM interviewer evaluation score ─────────────────────────────────────

class LLMEvaluationScore(BaseModel):
    """
    Qualitative scores from the LLM acting as a senior technical interviewer.
    Each dimension has a score AND an explanation so every number is justified.
    """
    technical_depth:       float = 0.0   # 0–10
    technical_feedback:    str   = ""

    reasoning_quality:     float = 0.0   # 0–10
    reasoning_feedback:    str   = ""

    problem_solving:       float = 0.0   # 0–10
    problem_solving_feedback: str = ""

    trade_off_thinking:    float = 0.0   # 0–10
    trade_off_feedback:    str   = ""

    answer_maturity:       float = 0.0   # 0–10  (seniority signal)
    maturity_feedback:     str   = ""

    overall_llm_score:     float = 0.0   # 0–10 (derived or directly from LLM)
    interviewer_summary:   str   = ""    # 2–3 sentence qualitative debrief
    follow_up_questions:   list[str] = []  # what a real interviewer would probe next

    @model_validator(mode="after")
    def derive_overall(self) -> "LLMEvaluationScore":
        """If overall not explicitly set, compute from the five dimensions."""
        if self.overall_llm_score == 0.0:
            self.overall_llm_score = round(
                (self.technical_depth + self.reasoning_quality +
                 self.problem_solving + self.trade_off_thinking +
                 self.answer_maturity) / 5,
                1,
            )
        return self


# ── QuestionEvaluation ─────────────────────────────────────────────────────────

class QuestionEvaluation(BaseModel):
    qa_pair:           QAPair
    star_score:        STARScore
    communication:     CommunicationScore
    improvement_tips:  list[str]          = []
    flagged_off_topic: bool               = False

    # Phase 2 additions — optional so legacy code keeps working
    rule_based_score:  Optional[RuleBasedScore]  = None
    llm_eval_score:    Optional[LLMEvaluationScore] = None

    @property
    def composite_score(self) -> float:
        """
        Hybrid scoring when new evaluators are present; falls back to the
        original formula for backward compatibility.
        """
        comm_scaled = self.communication.score / 10 * 100

        if self.llm_eval_score is not None and self.rule_based_score is not None:
            # Full hybrid formula (weights from config, hardcoded defaults here)
            llm_scaled  = self.llm_eval_score.overall_llm_score / 10 * 100
            rule_scaled = self.rule_based_score.composite / 10 * 100
            return round(
                llm_scaled   * 0.40 +
                rule_scaled  * 0.35 +
                comm_scaled  * 0.25,
                1,
            )

        if self.rule_based_score is not None:
            # Rule-based + legacy STAR + communication
            star_scaled = self.star_score.total / 10 * 100
            rule_scaled = self.rule_based_score.composite / 10 * 100
            return round(
                star_scaled  * 0.30 +
                rule_scaled  * 0.35 +
                comm_scaled  * 0.35,
                1,
            )

        # Original formula — no new evaluators
        star_scaled = self.star_score.total / 10 * 100
        return round(
            star_scaled * 0.40 +
            comm_scaled * 0.30 +
            (1 - self.flagged_off_topic) * comm_scaled * 0.30,
            1,
        )


# ── ReadinessReport ────────────────────────────────────────────────────────────

class ReadinessReport(BaseModel):
    candidate_name:           Optional[str]           = None
    role:                     str
    jd_summary:               ParsedJD
    evaluations:              list[QuestionEvaluation]
    overall_score:            float
    overall_tier:             ReadinessTier
    top_strengths:            list[str]
    top_gaps:                 list[str]
    practice_recommendations: list[str]

    @field_validator("top_strengths", "top_gaps")
    @classmethod
    def at_least_one(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("must have at least 1 item")
        return v

    @field_validator("practice_recommendations")
    @classmethod
    def at_least_three(cls, v: list[str]) -> list[str]:
        if len(v) < 3:
            raise ValueError("must have at least 3 items")
        return v

    @classmethod
    def from_evaluations(
        cls,
        evaluations: list[QuestionEvaluation],
        jd: ParsedJD,
        candidate_name: Optional[str] = None,
    ) -> "ReadinessReport":
        """Factory: build report from a list of evaluations."""
        scores    = [e.composite_score for e in evaluations]
        avg_score = round(sum(scores) / len(scores), 1)

        if avg_score >= 75:
            tier = ReadinessTier.EXCELLENT
        elif avg_score >= 50:
            tier = ReadinessTier.GOOD
        else:
            tier = ReadinessTier.NEEDS_WORK

        # ── Derive strengths ───────────────────────────────────────────────
        strengths: list[str] = []

        avg_star = sum(e.star_score.total for e in evaluations) / len(evaluations)
        avg_comm = sum(e.communication.score for e in evaluations) / len(evaluations)

        if avg_star >= 6.0:
            strengths.append("Describes concrete, first-person actions taken")
        if avg_comm >= 6.0:
            strengths.append("Communicates clearly and concisely")

        # Check STAR components
        sit_avg = sum(e.star_score.situation_score for e in evaluations) / len(evaluations)
        act_avg = sum(e.star_score.action_score for e in evaluations) / len(evaluations)
        res_avg = sum(e.star_score.result_score for e in evaluations) / len(evaluations)

        if sit_avg >= 6.0:
            strengths.append("Clearly sets up the context (Situation) for each answer")
        if act_avg >= 7.0:
            strengths.append("Provides detailed, specific Action steps")
        if res_avg >= 6.0:
            strengths.append("Articulates outcomes and measurable results")

        # Rule-based strengths
        rb_evals = [e.rule_based_score for e in evaluations if e.rule_based_score]
        if rb_evals:
            avg_ownership = sum(r.ownership_score for r in rb_evals) / len(rb_evals)
            avg_impact    = sum(r.impact_score for r in rb_evals) / len(rb_evals)
            avg_skill     = sum(r.skill_coverage_pct for r in rb_evals) / len(rb_evals)
            if avg_ownership >= 7.0:
                strengths.append("Uses strong ownership language throughout answers")
            if avg_impact >= 7.0:
                strengths.append("Backs claims with quantified impact and results")
            if avg_skill >= 60:
                strengths.append("Demonstrates good coverage of required skills")

        # LLM-eval strengths
        llm_evals = [e.llm_eval_score for e in evaluations if e.llm_eval_score]
        if llm_evals:
            avg_depth    = sum(l.technical_depth for l in llm_evals) / len(llm_evals)
            avg_maturity = sum(l.answer_maturity for l in llm_evals) / len(llm_evals)
            if avg_depth >= 7.0:
                strengths.append("Demonstrates strong technical depth in answers")
            if avg_maturity >= 7.0:
                strengths.append("Answers reflect senior-level thinking and ownership")

        if not strengths:
            strengths.append("Attempts to address all questions asked")

        # ── Derive gaps ────────────────────────────────────────────────────
        gaps: list[str] = []

        off_topic = sum(1 for e in evaluations if e.flagged_off_topic)
        if off_topic > 0:
            gaps.append("Some answers drift off-topic — re-read the question before answering")

        missing_components = []
        for e in evaluations:
            missing_components.extend(e.star_score.missing_components)
        if missing_components:
            most_missed = max(set(missing_components), key=missing_components.count)
            gaps.append(f"STAR '{most_missed}' component is frequently underdeveloped")

        if avg_comm < 6.0:
            gaps.append("Communication clarity needs improvement — aim for shorter sentences")

        if rb_evals:
            if sum(r.impact_score for r in rb_evals) / len(rb_evals) < 5.0:
                gaps.append("Answers lack quantified impact — add numbers, percentages, and timelines")
            if sum(r.ownership_score for r in rb_evals) / len(rb_evals) < 5.0:
                gaps.append("Use more first-person ownership language ('I designed', 'I led')")
            if sum(r.skill_coverage_pct for r in rb_evals) / len(rb_evals) < 40:
                gaps.append("Answers don't reference enough skills from the job description")

        if llm_evals:
            if sum(l.trade_off_thinking for l in llm_evals) / len(llm_evals) < 5.0:
                gaps.append("Rarely discusses trade-offs or alternative approaches considered")
            if sum(l.reasoning_quality for l in llm_evals) / len(llm_evals) < 5.0:
                gaps.append("Explain your reasoning process, not just what you did")

        if not gaps:
            gaps.append("Continue practising to build consistency across all question types")

        # ── Recommendations ────────────────────────────────────────────────
        recs: list[str] = [
            "Practice structuring every answer with Situation, Task, Action, and Result.",
            "Record yourself answering and review for filler words and pacing.",
            "Prepare 2–3 quantified achievements you can adapt across multiple questions.",
            "Research the company's tech stack and weave relevant keywords into answers.",
            "Practice answering trade-off questions: 'Why did you choose X over Y?'",
        ]

        return cls(
            candidate_name=candidate_name,
            role=jd.role_title,
            jd_summary=jd,
            evaluations=evaluations,
            overall_score=avg_score,
            overall_tier=tier,
            top_strengths=strengths[:3],
            top_gaps=gaps[:3],
            practice_recommendations=recs,
        )
