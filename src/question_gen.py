"""
question_gen.py — Module 2: Question Generator
Uses an LLM (Gemini) + the question_gen.txt prompt to generate a
validated QuestionBank from a ParsedJD.
"""

import json
import re
from pathlib import Path

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from .schemas import ParsedJD, Question, QuestionBank, QuestionType, Difficulty

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class QuestionGenerator:
    """
    Generates a role-specific QuestionBank from a ParsedJD using an LLM.

    Usage:
        gen = QuestionGenerator()                 # uses GEMINI_API_KEY from env
        bank = gen.generate(parsed_jd)
    """

    def __init__(self, llm=None, api_key: str | None = None):
        if llm is None:
            kwargs = {"model": "gemini-2.5-flash", "temperature": 0.4}
            if api_key:
                kwargs["google_api_key"] = api_key
            llm = ChatGoogleGenerativeAI(**kwargs)
        self.llm = llm

        prompt_text = (PROMPTS_DIR / "question_gen.txt").read_text()
        self.prompt = PromptTemplate(
            input_variables=[
                "role", "experience_level", "required_skills",
                "tech_stack", "responsibilities",
            ],
            template=prompt_text,
        )
        self.chain = self.prompt | self.llm

    # ─────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ─────────────────────────────────────

    def generate(self, jd: ParsedJD) -> QuestionBank:
        """
        Calls the LLM to generate 10 questions for the given parsed JD,
        validates and wraps them in a QuestionBank.
        """
        raw = self.chain.invoke({
            "role":             jd.role_title,
            "experience_level": jd.experience_level,
            "required_skills":  ", ".join(jd.required_skills) or "Not specified",
            "tech_stack":       ", ".join(jd.tech_stack) or "Not specified",
            "responsibilities": "; ".join(jd.responsibilities) or "Not specified",
        })

        questions_data = self._parse_response(raw.content)
        questions = [self._build_question(q, idx) for idx, q in enumerate(questions_data, start=1)]

        # Safety net: if LLM returned fewer than 5 valid questions, pad with
        # generic fallback questions so QuestionBank validation still passes.
        if len(questions) < 5:
            questions += self._fallback_questions(jd, start_idx=len(questions) + 1)

        return QuestionBank(role=jd.role_title, questions=questions)

    # ─────────────────────────────────────
    # RESPONSE PARSING
    # ─────────────────────────────────────

    @staticmethod
    def _parse_response(text: str) -> list[dict]:
        """
        Cleans and parses the LLM's JSON array response.
        Handles markdown fences and minor formatting issues gracefully.
        """
        cleaned = re.sub(r"```(?:json)?", "", text).strip()

        # Extract the first [...] block in case the model adds extra text
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return []

        if not isinstance(data, list):
            return []

        return data

    @staticmethod
    def _build_question(raw: dict, idx: int) -> Question:
        """
        Converts a raw dict from the LLM into a validated Question object.
        Applies safe defaults for any missing/invalid fields.
        """
        qid = raw.get("id") or f"Q{idx:02d}"

        qtype_raw = str(raw.get("type", "behavioural")).lower().replace(" ", "_")
        try:
            qtype = QuestionType(qtype_raw)
        except ValueError:
            qtype = QuestionType.BEHAVIOURAL

        diff_raw = str(raw.get("difficulty", "medium")).lower()
        try:
            difficulty = Difficulty(diff_raw)
        except ValueError:
            difficulty = Difficulty.MEDIUM

        text = str(raw.get("text", "")).strip() or "Tell me about a relevant experience for this role."

        ideal_topics = raw.get("ideal_topics", [])
        if not isinstance(ideal_topics, list):
            ideal_topics = []
        ideal_topics = [str(t) for t in ideal_topics][:5]

        star_applicable = bool(raw.get("star_applicable", qtype in (
            QuestionType.BEHAVIOURAL, QuestionType.SITUATIONAL
        )))

        return Question(
            id=qid,
            text=text,
            type=qtype,
            difficulty=difficulty,
            star_applicable=star_applicable,
            ideal_topics=ideal_topics,
        )

    # ─────────────────────────────────────
    # FALLBACK QUESTIONS
    # ─────────────────────────────────────

    @staticmethod
    def _fallback_questions(jd: ParsedJD, start_idx: int) -> list[Question]:
        """
        Generic role-agnostic questions used only if the LLM response
        was malformed or returned too few questions. Ensures QuestionBank
        always has at least 5 valid entries.
        """
        templates = [
            ("Tell me about a time you had to learn a new skill quickly to complete a project.",
             QuestionType.BEHAVIOURAL, True, ["adaptability", "learning"]),
            (f"What experience do you have with {', '.join(jd.tech_stack[:2]) or 'the tools required for this role'}?",
             QuestionType.TECHNICAL, False, ["technical depth"]),
            ("How would you approach a situation where you disagree with a team decision?",
             QuestionType.SITUATIONAL, True, ["collaboration", "conflict resolution"]),
            ("Describe a project you're proud of and what made it successful.",
             QuestionType.BEHAVIOURAL, True, ["ownership", "impact"]),
            ("What motivates you about this role and our company?",
             QuestionType.CULTURE_FIT, False, ["motivation", "alignment"]),
        ]

        result = []
        for i, (text, qtype, star, topics) in enumerate(templates):
            result.append(Question(
                id=f"Q{start_idx + i:02d}",
                text=text,
                type=qtype,
                difficulty=Difficulty.MEDIUM,
                star_applicable=star,
                ideal_topics=topics,
            ))
        return result
