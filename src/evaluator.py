"""
evaluator.py — Module 4: Evaluation Engine
Three sub-evaluators that run on each Q&A pair, then combine into a composite score.
"""

import json
import re
from pathlib import Path

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from .schemas import (
    QAPair, STARScore, CommunicationScore,
    QuestionEvaluation, Question
)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


# ─────────────────────────────────────────
# STAR SCORER
# ─────────────────────────────────────────

class STARScorer:
    """
    Uses an LLM to score a candidate's answer on all 4 STAR components.
    Returns a STARScore Pydantic object.
    """

    def __init__(self, llm):
        self.llm = llm
        prompt_text = (PROMPTS_DIR / "star_scorer.txt").read_text()
        self.prompt = PromptTemplate(
            input_variables=["question", "answer"],
            template=prompt_text,
        )
        self.chain = self.prompt | self.llm

    def score(self, question: str, answer: str) -> STARScore:
        raw = self.chain.invoke({"question": question, "answer": answer})
        clean = self._clean_json(raw.content)
        data = json.loads(clean)
        return STARScore(**data)

    @staticmethod
    def _clean_json(text: str) -> str:
        """Strip markdown fences if LLM wraps output despite instructions."""
        text = re.sub(r"```(?:json)?", "", text).strip()
        return text


# ─────────────────────────────────────────
# CONTENT RELEVANCE EVALUATOR
# ─────────────────────────────────────────

class ContentRelevanceEvaluator:
    """
    No LLM needed — uses sentence-transformers cosine similarity.
    Compares the semantic meaning of the answer against the question.
    """

    def __init__(self):
        from sentence_transformers import SentenceTransformer, util
        self._model = SentenceTransformer("all-MiniLM-L6-v2")
        self._util  = util

    def score(self, question: str, answer: str) -> float:
        """Returns cosine similarity in [0, 1]. Below 0.4 = off-topic."""
        q_emb = self._model.encode(question, convert_to_tensor=True)
        a_emb = self._model.encode(answer,   convert_to_tensor=True)
        sim = self._util.cos_sim(q_emb, a_emb).item()
        return round(float(sim), 4)

    def is_off_topic(self, question: str, answer: str, threshold: float = 0.4) -> bool:
        return self.score(question, answer) < threshold


# ─────────────────────────────────────────
# COMMUNICATION QUALITY EVALUATOR
# ─────────────────────────────────────────

FILLER_WORDS = {
    "um", "uh", "like", "basically", "literally",
    "you know", "sort of", "kind of", "actually",
    "so yeah", "right", "honestly", "obviously",
}

class CommunicationEvaluator:
    """
    No LLM needed — pure NLP using spaCy + textstat.
    Analyses clarity, conciseness, filler words, passive voice.
    """

    def __init__(self):
        import spacy, textstat
        self.nlp      = spacy.load("en_core_web_sm")
        self.textstat = textstat

    def score(self, answer: str) -> CommunicationScore:
        doc   = self.nlp(answer)
        words = [t.text.lower() for t in doc if not t.is_punct and not t.is_space]

        # Filler word count
        filler_count = sum(
            1 for token in words if token in FILLER_WORDS
        )

        # Passive voice: look for "was/were/been + VBN" pattern
        passive_sentences = 0
        total_sentences   = len(list(doc.sents))
        for sent in doc.sents:
            sent_tokens = [t for t in sent]
            for i, t in enumerate(sent_tokens):
                if t.lemma_ in ("be", "been", "was", "were"):
                    # check if a past participle follows nearby
                    rest = sent_tokens[i+1:i+4]
                    if any(r.tag_ == "VBN" for r in rest):
                        passive_sentences += 1
                        break

        passive_pct = round(
            (passive_sentences / total_sentences * 100) if total_sentences else 0, 1
        )

        # Vocabulary diversity (type-token ratio)
        unique_words   = set(words)
        ttr            = round(len(unique_words) / len(words), 4) if words else 0

        # Average sentence length
        sent_lengths   = [len([t for t in s if not t.is_punct]) for s in doc.sents]
        avg_sent_len   = round(sum(sent_lengths) / len(sent_lengths), 1) if sent_lengths else 0

        return CommunicationScore(
            reading_ease       = round(self.textstat.flesch_reading_ease(answer), 1),
            avg_sentence_len   = avg_sent_len,
            filler_word_count  = filler_count,
            passive_voice_pct  = passive_pct,
            vocabulary_diversity = ttr,
            word_count         = len(words),
        )


# ─────────────────────────────────────────
# FEEDBACK GENERATOR
# ─────────────────────────────────────────

class FeedbackGenerator:
    """Generates 2 specific, actionable improvement tips per answer via LLM."""

    def __init__(self, llm):
        self.llm   = llm
        prompt_text = (PROMPTS_DIR / "feedback_gen.txt").read_text()
        self.prompt = PromptTemplate(
            input_variables=[
                "question", "answer", "star_total",
                "missing_components", "relevance",
                "comm_score", "composite",
            ],
            template=prompt_text,
        )
        self.chain = self.prompt | self.llm

    def generate(
        self,
        question:           str,
        answer:             str,
        star_score:         STARScore,
        relevance:          float,
        comm_score:         CommunicationScore,
        composite:          float,
    ) -> list[str]:
        missing = star_score.missing_components or ["none"]
        raw = self.chain.invoke({
            "question":           question,
            "answer":             answer,
            "star_total":         f"{star_score.total:.1f}",
            "missing_components": ", ".join(missing),
            "relevance":          f"{relevance * 10:.1f}",
            "comm_score":         f"{comm_score.score:.1f}",
            "composite":          f"{composite:.1f}",
        })
        clean = re.sub(r"```(?:json)?", "", raw.content).strip()
        tips  = json.loads(clean)
        return tips[:2]


# ─────────────────────────────────────────
# MAIN EVALUATION PIPELINE
# ─────────────────────────────────────────

class EvaluationEngine:
    """
    Orchestrates all 3 sub-evaluators for a single Q&A pair.
    Returns a fully populated QuestionEvaluation object.

    Usage:
        engine = EvaluationEngine()
        result = engine.evaluate(qa_pair)
    """

    def __init__(self, api_key: str | None = None):
        kwargs = {"model": "gemini-2.5-flash", "temperature": 0}
        if api_key:
            kwargs["google_api_key"] = api_key
        llm = ChatGoogleGenerativeAI(**kwargs)

        self.star_scorer       = STARScorer(llm)
        self.relevance_eval    = ContentRelevanceEvaluator()
        self.comm_eval         = CommunicationEvaluator()
        self.feedback_gen      = FeedbackGenerator(llm)

    def evaluate(self, qa_pair: QAPair) -> QuestionEvaluation:
        q_text = qa_pair.question.text
        a_text = qa_pair.answer

        # Run all 3 evaluators
        star      = self.star_scorer.score(q_text, a_text)
        relevance = self.relevance_eval.score(q_text, a_text)
        comm      = self.comm_eval.score(a_text)

        # Build partial evaluation to compute composite for feedback prompt
        partial = QuestionEvaluation(
            qa_pair           = qa_pair,
            star_score        = star,
            content_relevance = relevance,
            communication     = comm,
            improvement_tips  = ["placeholder"],   # overwritten below
            flagged_off_topic = relevance < 0.4,
        )

        tips = self.feedback_gen.generate(
            question    = q_text,
            answer      = a_text,
            star_score  = star,
            relevance   = relevance,
            comm_score  = comm,
            composite   = partial.composite_score,
        )

        return QuestionEvaluation(
            qa_pair           = qa_pair,
            star_score        = star,
            content_relevance = relevance,
            communication     = comm,
            improvement_tips  = tips,
            flagged_off_topic = relevance < 0.4,
        )

    def evaluate_all(self, qa_pairs: list[QAPair]) -> list[QuestionEvaluation]:
        """Evaluate a full list of Q&A pairs in sequence."""
        return [self.evaluate(pair) for pair in qa_pairs]
