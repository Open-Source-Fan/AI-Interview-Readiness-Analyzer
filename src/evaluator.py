"""
evaluator.py — Module 4: Evaluation Engine

Five evaluators run on each Q&A pair and combine into a hybrid composite score.

Existing evaluators (unchanged):
    STARScorer                — LLM: STAR completeness
    ContentRelevanceEvaluator — sentence-transformers: cosine similarity
    CommunicationEvaluator    — spaCy + textstat: clarity metrics
    FeedbackGenerator         — LLM: 2 actionable improvement tips

New evaluators (Phase 2 additions):
    RuleBasedScorer  — pure Python/regex: ownership, impact, skills, STAR, length
    LLMEvaluator     — LLM as senior interviewer: depth, reasoning, maturity

Backward-compatible: existing tests and demo_pipeline.py work unchanged.
parsed_jd is optional — when omitted, new evaluators use neutral defaults.
"""

import json
import re
from pathlib import Path

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from .schemas import (
    CommunicationScore,
    ParsedJD,
    QAPair,
    QuestionEvaluation,
    STARScore,
)
from .rule_based_scorer import RuleBasedScorer
from .llm_evaluator import LLMEvaluator

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


# ── Sub-evaluator 1: STAR scorer ──────────────────────────────────────────────

class STARScorer:
    """
    Uses an LLM to evaluate the STAR completeness of a candidate answer.
    Returns a STARScore with per-component scores and evidence quotes.
    """

    def __init__(self, llm) -> None:
        self.llm = llm
        prompt_text = (PROMPTS_DIR / "star_scorer.txt").read_text(encoding="utf-8")
        self.prompt = PromptTemplate(
            input_variables=["question", "answer"],
            template=prompt_text,
        )
        self.chain = self.prompt | self.llm

    def score(self, question: str, answer: str) -> STARScore:
        try:
            response = self.chain.invoke({"question": question, "answer": answer})
            raw = response.content

            # Strip markdown fences
            cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                return STARScore()

            json_str = match.group(0)
            json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
            data = json.loads(json_str)

            return STARScore(
                situation_score=float(data.get("situation_score", 0)),
                task_score=float(data.get("task_score", 0)),
                action_score=float(data.get("action_score", 0)),
                result_score=float(data.get("result_score", 0)),
                situation_evidence=str(data.get("situation_evidence", "not mentioned")),
                task_evidence=str(data.get("task_evidence", "not mentioned")),
                action_evidence=str(data.get("action_evidence", "not mentioned")),
                result_evidence=str(data.get("result_evidence", "not mentioned")),
            )
        except Exception:  # noqa: BLE001
            return STARScore()


# ── Sub-evaluator 2: Content relevance ────────────────────────────────────────

class ContentRelevanceEvaluator:
    """
    Cosine similarity between question and answer using sentence-transformers.
    No API cost. Flags off-topic answers below a threshold.
    """

    THRESHOLD = 0.40

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def score(self, question: str, answer: str) -> tuple[float, bool]:
        """Returns (similarity 0-1, flagged_off_topic bool)."""
        import numpy as np
        q_emb = self.model.encode([question])
        a_emb = self.model.encode([answer])
        cos_sim = float(
            np.dot(q_emb[0], a_emb[0]) /
            (np.linalg.norm(q_emb[0]) * np.linalg.norm(a_emb[0]) + 1e-9)
        )
        cos_sim = max(0.0, min(1.0, cos_sim))
        return cos_sim, cos_sim < self.THRESHOLD


# ── Sub-evaluator 3: Communication quality ────────────────────────────────────

class CommunicationEvaluator:
    """
    spaCy + textstat analysis: reading ease, filler words, passive voice,
    sentence length, vocabulary diversity, word count.
    No API cost.
    """

    FILLER_WORDS = {
        "um", "uh", "like", "basically", "literally", "actually",
        "you know", "sort of", "kind of", "right", "okay", "so",
    }

    def __init__(self) -> None:
        import spacy
        self.nlp = spacy.load("en_core_web_sm")

    def score(self, answer: str) -> CommunicationScore:
        import textstat

        doc = self.nlp(answer)
        words = [t.text.lower() for t in doc if not t.is_punct and not t.is_space]
        sentences = list(doc.sents)

        word_count = len(words)
        avg_sentence_len = word_count / max(len(sentences), 1)
        filler_count = sum(1 for w in words if w in self.FILLER_WORDS)

        passive_count = sum(
            1 for sent in sentences
            if any(
                t.dep_ == "auxpass" or (t.dep_ == "nsubjpass")
                for t in sent
            )
        )
        passive_ratio = passive_count / max(len(sentences), 1)

        unique_words = {w for w in words if w.isalpha()}
        vocab_diversity = len(unique_words) / max(word_count, 1)
        reading_ease = textstat.flesch_reading_ease(answer)

        return CommunicationScore(
            reading_ease=reading_ease,
            avg_sentence_len=avg_sentence_len,
            filler_word_count=filler_count,
            passive_voice_ratio=passive_ratio,
            vocabulary_diversity=vocab_diversity,
            word_count=word_count,
        )


# ── Sub-evaluator 4: Feedback generator ───────────────────────────────────────

class FeedbackGenerator:
    """
    Uses an LLM to generate 2 specific, actionable improvement tips
    based on the evaluation scores and the candidate's answer.
    """

    def __init__(self, llm) -> None:
        self.llm = llm
        prompt_text = (PROMPTS_DIR / "feedback_gen.txt").read_text(encoding="utf-8")
        self.prompt = PromptTemplate(
            input_variables=[
                "question", "answer", "star_total", "missing_components",
                "relevance", "comm_score", "composite",
            ],
            template=prompt_text,
        )
        self.chain = self.prompt | self.llm

    def generate(
        self,
        qa_pair: QAPair,
        star_total: float,
        missing_components: list[str],
        relevance: float,
        comm_score: float,
        composite: float,
    ) -> list[str]:
        try:
            response = self.chain.invoke({
                "question": qa_pair.question.text,
                "answer": qa_pair.answer,
                "star_total": round(star_total, 1),
                "missing_components": ", ".join(missing_components) or "none",
                "relevance": round(relevance * 100, 1),
                "comm_score": round(comm_score, 1),
                "composite": round(composite, 1),
            })
            raw = response.content
            cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")
            match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if match:
                tips = json.loads(match.group(0))
                if isinstance(tips, list):
                    return [str(t) for t in tips[:2]]
        except Exception:  # noqa: BLE001
            pass
        return [
            "Be more specific about the actions YOU personally took.",
            "Quantify your results with concrete metrics (%, time saved, users affected).",
        ]


# ── Main evaluation engine ────────────────────────────────────────────────────

class EvaluationEngine:
    """
    Orchestrates all 5 evaluators for a single Q&A pair.
    Returns a fully populated QuestionEvaluation object.

    Usage:
        engine = EvaluationEngine()

        # Basic (no JD context):
        result = engine.evaluate(qa_pair)

        # Full hybrid (with JD context for skill coverage + LLM role context):
        result = engine.evaluate(qa_pair, parsed_jd=parsed_jd)

    The evaluate_all() helper runs all Q&A pairs and passes parsed_jd through.
    """

    def __init__(self, api_key: str | None = None) -> None:
        kwargs: dict = {"model": "gemini-2.5-flash", "temperature": 0}
        if api_key:
            kwargs["google_api_key"] = api_key
        llm = ChatGoogleGenerativeAI(**kwargs)

        # Existing evaluators
        self.star_scorer    = STARScorer(llm)
        self.relevance_eval = ContentRelevanceEvaluator()
        self.comm_eval      = CommunicationEvaluator()
        self.feedback_gen   = FeedbackGenerator(llm)

        # New Phase 2 evaluators
        self.rule_scorer = RuleBasedScorer()
        self.llm_eval    = LLMEvaluator(llm)

    def evaluate(
        self,
        qa_pair: QAPair,
        parsed_jd: ParsedJD | None = None,
    ) -> QuestionEvaluation:
        """
        Evaluate one Q&A pair.
        parsed_jd is optional — if omitted, rule-based and LLM evaluators
        use neutral defaults and all existing tests continue to pass.
        """
        q_text = qa_pair.question.text
        a_text = qa_pair.answer

        # ── Existing three evaluators ──────────────────────────────────────
        star = self.star_scorer.score(q_text, a_text)
        relevance, flagged = self.relevance_eval.score(q_text, a_text)
        comm = self.comm_eval.score(a_text)

        # ── New two evaluators ─────────────────────────────────────────────
        rule_based = self.rule_scorer.score(
            answer=a_text,
            question=qa_pair.question,
            parsed_jd=parsed_jd,
        )
        llm_eval = self.llm_eval.evaluate(
            qa_pair=qa_pair,
            parsed_jd=parsed_jd,
        )

        # ── Partial evaluation (needed to compute composite for tips) ──────
        partial = QuestionEvaluation(
            qa_pair=qa_pair,
            star_score=star,
            communication=comm,
            flagged_off_topic=flagged,
            rule_based_score=rule_based,
            llm_eval_score=llm_eval,
        )

        # ── Feedback uses composite (now the hybrid score if new fields set) -
        tips = self.feedback_gen.generate(
            qa_pair=qa_pair,
            star_total=star.total,
            missing_components=star.missing_components,
            relevance=relevance,
            comm_score=comm.score,
            composite=partial.composite_score,
        )

        return QuestionEvaluation(
            qa_pair=qa_pair,
            star_score=star,
            communication=comm,
            improvement_tips=tips,
            flagged_off_topic=flagged,
            rule_based_score=rule_based,
            llm_eval_score=llm_eval,
        )

    def evaluate_all(
        self,
        qa_pairs: list[QAPair],
        parsed_jd: ParsedJD | None = None,
    ) -> list[QuestionEvaluation]:
        """Evaluate all Q&A pairs, passing parsed_jd to each."""
        return [self.evaluate(qa_pair, parsed_jd) for qa_pair in qa_pairs]
