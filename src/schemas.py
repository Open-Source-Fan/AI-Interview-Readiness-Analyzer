"""
schemas.py — All Pydantic models for the Interview Readiness Analyzer.
Every module imports from here. Never define data shapes anywhere else.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


# ─────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────

class QuestionType(str, Enum):
    BEHAVIOURAL  = "behavioural"
    TECHNICAL    = "technical"
    SITUATIONAL  = "situational"
    CULTURE_FIT  = "culture_fit"

class Difficulty(str, Enum):
    EASY   = "easy"
    MEDIUM = "medium"
    HARD   = "hard"

class ReadinessTier(str, Enum):
    EXCELLENT   = "Excellent"
    GOOD        = "Good"
    NEEDS_WORK  = "Needs Work"


# ─────────────────────────────────────────
# MODULE 1 — JD PARSER OUTPUT
# ─────────────────────────────────────────

class ParsedJD(BaseModel):
    """Structured output from the JD parser module."""
    raw_text:         str            = Field(..., description="Original JD text")
    role_title:       str            = Field(..., description="Inferred job title")
    experience_level: str            = Field(..., description="e.g. Junior / Mid / Senior")
    required_skills:  list[str]      = Field(default_factory=list, description="Hard skills extracted")
    nice_to_have:     list[str]      = Field(default_factory=list, description="Preferred but not required skills")
    tech_stack:       list[str]      = Field(default_factory=list, description="Technologies mentioned")
    responsibilities: list[str]      = Field(default_factory=list, description="Key job responsibilities")

    @field_validator("role_title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("role_title cannot be empty")
        return v.strip()


# ─────────────────────────────────────────
# MODULE 2 — QUESTION GENERATOR OUTPUT
# ─────────────────────────────────────────

class Question(BaseModel):
    """A single interview question with metadata."""
    id:               str            = Field(..., description="Unique ID e.g. Q01")
    text:             str            = Field(..., description="The question text")
    type:             QuestionType
    difficulty:       Difficulty
    star_applicable:  bool           = Field(..., description="Should answer follow STAR structure?")
    ideal_topics:     list[str]      = Field(default_factory=list, description="Topics a good answer should cover")

class QuestionBank(BaseModel):
    """Full set of questions generated for one JD."""
    role:       str
    questions:  list[Question]

    @field_validator("questions")
    @classmethod
    def minimum_questions(cls, v: list) -> list:
        if len(v) < 5:
            raise ValueError("QuestionBank must contain at least 5 questions")
        return v

    def by_type(self, qtype: QuestionType) -> list[Question]:
        return [q for q in self.questions if q.type == qtype]


# ─────────────────────────────────────────
# MODULE 3 — RESPONSE COLLECTOR OUTPUT
# ─────────────────────────────────────────

class QAPair(BaseModel):
    """One question + the candidate's answer."""
    question:   Question
    answer:     str     = Field(..., description="Candidate's raw answer text")
    duration_s: Optional[int] = Field(None, description="Time taken to answer in seconds")

    @field_validator("answer")
    @classmethod
    def answer_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Answer cannot be empty")
        return v.strip()


# ─────────────────────────────────────────
# MODULE 4 — EVALUATION ENGINE OUTPUT
# ─────────────────────────────────────────

class STARScore(BaseModel):
    """STAR method breakdown for one answer."""
    situation_score: float = Field(..., ge=0, le=10)
    task_score:      float = Field(..., ge=0, le=10)
    action_score:    float = Field(..., ge=0, le=10)
    result_score:    float = Field(..., ge=0, le=10)

    situation_evidence: str = Field(..., description="Quote or note supporting the score")
    task_evidence:      str
    action_evidence:    str
    result_evidence:    str

    @property
    def total(self) -> float:
        return round((self.situation_score + self.task_score +
                      self.action_score + self.result_score) / 4, 2)

    @property
    def missing_components(self) -> list[str]:
        missing = []
        if self.situation_score < 3: missing.append("Situation")
        if self.task_score      < 3: missing.append("Task")
        if self.action_score    < 3: missing.append("Action")
        if self.result_score    < 3: missing.append("Result")
        return missing


class CommunicationScore(BaseModel):
    """Communication quality metrics for one answer."""
    reading_ease:       float = Field(..., ge=0,  le=100, description="Flesch reading ease")
    avg_sentence_len:   float = Field(..., ge=0,  description="Words per sentence")
    filler_word_count:  int   = Field(..., ge=0,  description="um/uh/like/basically count")
    passive_voice_pct:  float = Field(..., ge=0,  le=100, description="% passive voice sentences")
    vocabulary_diversity: float = Field(..., ge=0, le=1,  description="Type-token ratio")
    word_count:         int   = Field(..., ge=0)

    @property
    def score(self) -> float:
        """0–10 communication score. Higher is better."""
        s = 5.0
        if self.reading_ease       > 60:  s += 1.5
        elif self.reading_ease     < 30:  s -= 1.5
        if self.filler_word_count  == 0:  s += 1.0
        elif self.filler_word_count > 5:  s -= 1.5
        if self.passive_voice_pct  < 20:  s += 1.0
        elif self.passive_voice_pct > 50: s -= 1.0
        if self.vocabulary_diversity > 0.6: s += 0.5
        return round(max(0, min(10, s)), 2)


class QuestionEvaluation(BaseModel):
    """Full evaluation result for a single Q&A pair."""
    qa_pair:              QAPair
    star_score:           STARScore
    content_relevance:    float  = Field(..., ge=0, le=1, description="Cosine similarity score")
    communication:        CommunicationScore
    improvement_tips:     list[str] = Field(..., min_length=1, max_length=3)
    flagged_off_topic:    bool  = Field(False)

    @property
    def composite_score(self) -> float:
        """Weighted composite: STAR 40% + relevance 30% + communication 30%."""
        star_norm  = (self.star_score.total / 10) * 100
        rel_norm   = self.content_relevance * 100
        comm_norm  = (self.communication.score / 10) * 100
        return round(star_norm * 0.4 + rel_norm * 0.3 + comm_norm * 0.3, 1)

    @property
    def tier(self) -> ReadinessTier:
        s = self.composite_score
        if s >= 75: return ReadinessTier.EXCELLENT
        if s >= 50: return ReadinessTier.GOOD
        return ReadinessTier.NEEDS_WORK


# ─────────────────────────────────────────
# MODULE 5 — REPORT GENERATOR OUTPUT
# ─────────────────────────────────────────

class ReadinessReport(BaseModel):
    """The complete interview readiness report for one session."""
    candidate_name:     Optional[str]
    role:               str
    jd_summary:         ParsedJD

    evaluations:        list[QuestionEvaluation]

    overall_score:      float   = Field(..., ge=0, le=100)
    overall_tier:       ReadinessTier

    top_strengths:      list[str] = Field(..., min_length=1, max_length=3)
    top_gaps:           list[str] = Field(..., min_length=1, max_length=3)
    practice_recommendations: list[str] = Field(..., min_length=3, max_length=5)

    @classmethod
    def from_evaluations(
        cls,
        evaluations: list[QuestionEvaluation],
        jd: ParsedJD,
        candidate_name: Optional[str] = None,
    ) -> "ReadinessReport":
        """Factory: build report from a list of evaluations."""
        scores     = [e.composite_score for e in evaluations]
        avg_score  = round(sum(scores) / len(scores), 1)

        if avg_score >= 75: tier = ReadinessTier.EXCELLENT
        elif avg_score >= 50: tier = ReadinessTier.GOOD
        else: tier = ReadinessTier.NEEDS_WORK

        top_strengths, top_gaps = cls._derive_strengths_and_gaps(evaluations)
        practice_recommendations = cls._derive_recommendations(evaluations)

        return cls(
            candidate_name=candidate_name,
            role=jd.role_title,
            jd_summary=jd,
            evaluations=evaluations,
            overall_score=avg_score,
            overall_tier=tier,
            top_strengths=top_strengths,
            top_gaps=top_gaps,
            practice_recommendations=practice_recommendations,
        )

    @staticmethod
    def _derive_strengths_and_gaps(
        evaluations: list["QuestionEvaluation"],
    ) -> tuple[list[str], list[str]]:
        """
        Computes average scores across all evaluations and turns the
        highest-scoring areas into strengths and lowest-scoring areas
        into gaps. Always returns 1-3 strengths and 1-3 gaps.
        """
        n = len(evaluations)

        avg_situation = sum(e.star_score.situation_score for e in evaluations) / n
        avg_task      = sum(e.star_score.task_score      for e in evaluations) / n
        avg_action    = sum(e.star_score.action_score     for e in evaluations) / n
        avg_result    = sum(e.star_score.result_score     for e in evaluations) / n
        avg_comm      = sum(e.communication.score         for e in evaluations) / n
        avg_relevance = sum(e.content_relevance           for e in evaluations) / n
        avg_filler    = sum(e.communication.filler_word_count for e in evaluations) / n

        # Candidate metrics: (score on a 0-10 scale, strength label, gap label)
        candidates = [
            (avg_situation, "Clearly sets up the context (Situation) for each answer",
                             "Answers often lack clear context — set the scene before diving in"),
            (avg_task,      "Clearly defines personal responsibility (Task) in each answer",
                             "Personal responsibility (Task) is often unclear — state what YOU were tasked with"),
            (avg_action,    "Describes concrete, first-person actions taken",
                             "Actions described are often vague — use specific first-person steps"),
            (avg_result,    "Consistently quantifies outcomes and impact",
                             "Results are rarely quantified — add numbers, %, or measurable impact"),
            (avg_comm,      "Communicates clearly and concisely",
                             "Communication clarity needs work — reduce filler words and tighten sentences"),
            (avg_relevance * 10, "Answers stay tightly relevant to the question asked",
                             "Some answers drift off-topic — re-read the question before answering"),
        ]

        # Strengths: highest-scoring areas (score >= 7)
        strong = sorted([c for c in candidates if c[0] >= 7], key=lambda c: -c[0])
        top_strengths = [c[1] for c in strong[:3]]

        # Gaps: lowest-scoring areas (score < 6)
        weak = sorted([c for c in candidates if c[0] < 6], key=lambda c: c[0])
        top_gaps = [c[2] for c in weak[:3]]

        # Fallbacks to satisfy schema minimums (1-3 items each)
        if not top_strengths:
            top_strengths = ["Completed all interview questions with relevant answers"]
        if not top_gaps:
            if avg_filler > 2:
                top_gaps = ["Reduce filler words (um, uh, like, basically) for sharper delivery"]
            else:
                top_gaps = ["Continue practicing to push scores from 'Good' into 'Excellent'"]

        return top_strengths, top_gaps

    @staticmethod
    def _derive_recommendations(evaluations: list["QuestionEvaluation"]) -> list[str]:
        """
        Aggregates improvement tips from all evaluations, removes near-duplicates,
        and returns 3-5 recommendations (padding with generic tips if needed).
        """
        seen = set()
        unique_tips = []
        for e in evaluations:
            for tip in e.improvement_tips:
                key = tip.strip().lower()[:40]  # dedupe by first 40 chars
                if key not in seen:
                    seen.add(key)
                    unique_tips.append(tip.strip())

        generic_fallbacks = [
            "Practice structuring every answer with Situation, Task, Action, and Result.",
            "Record yourself answering and review for filler words and pacing.",
            "Prepare 2-3 quantified achievements you can adapt across multiple questions.",
            "Re-read each question carefully and address every part of it directly.",
            "Practice concise answers — aim for 60-90 seconds per response.",
        ]

        for fallback in generic_fallbacks:
            if len(unique_tips) >= 5:
                break
            key = fallback.strip().lower()[:40]
            if key not in seen:
                seen.add(key)
                unique_tips.append(fallback)

        # Ensure between 3 and 5 items
        if len(unique_tips) < 3:
            unique_tips += generic_fallbacks[:3 - len(unique_tips)]

        return unique_tips[:5]
