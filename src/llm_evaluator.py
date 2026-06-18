"""
llm_evaluator.py — Module 4c: LLM Interviewer Evaluation

Provider-agnostic: pass any LangChain-compatible chat model.
evaluate() accepts parsed_jd to give the LLM role/tech context.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.prompts import PromptTemplate

from .schemas import LLMEvaluationScore, QAPair

if TYPE_CHECKING:
    from .schemas import ParsedJD

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class LLMEvaluator:
    """
    Provider-agnostic LLM-based senior-interviewer evaluator.

    Usage:
        evaluator = LLMEvaluator(llm)
        score = evaluator.evaluate(qa_pair, parsed_jd=parsed_jd)
    """

    def __init__(self, llm) -> None:
        self.llm = llm
        prompt_text = (PROMPTS_DIR / "interviewer_eval.txt").read_text(encoding="utf-8")
        self.prompt = PromptTemplate(
            input_variables=["role", "experience_level", "tech_stack",
                             "question", "answer"],
            template=prompt_text,
        )
        self.chain = self.prompt | self.llm

    def evaluate(
        self,
        qa_pair: QAPair,
        parsed_jd: "ParsedJD | None" = None,
    ) -> LLMEvaluationScore:
        """
        Evaluate one Q&A pair. parsed_jd is optional — used to give the LLM
        role and tech-stack context. Falls back to neutral defaults if absent.
        """
        role            = parsed_jd.role_title if parsed_jd else "Software Engineer"
        experience_level = parsed_jd.experience_level if parsed_jd else "Mid"
        tech_stack_str  = (
            ", ".join(parsed_jd.tech_stack[:8]) if parsed_jd and parsed_jd.tech_stack
            else "not specified"
        )

        try:
            response = self.chain.invoke({
                "role":             role,
                "experience_level": experience_level,
                "tech_stack":       tech_stack_str,
                "question":         qa_pair.question.text,
                "answer":           qa_pair.answer,
            })
            return self._parse_response(response.content)
        except Exception as exc:  # noqa: BLE001
            return LLMEvaluationScore(
                interviewer_summary=f"Evaluation unavailable: {exc}",
            )

    # ── Private ───────────────────────────────────────────────────────────────

    def _parse_response(self, content: str) -> LLMEvaluationScore:
        cleaned  = re.sub(r"```(?:json)?", "", content).strip().rstrip("`")
        match    = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in LLM response")

        json_str = re.sub(r",\s*([}\]])", r"\1", match.group(0))
        data     = json.loads(json_str)

        def _f(key: str, default: float = 0.0) -> float:
            try: return round(float(data.get(key, default)), 1)
            except (TypeError, ValueError): return default

        def _s(key: str) -> str:
            return str(data.get(key, "")).strip()

        def _l(key: str) -> list[str]:
            v = data.get(key, [])
            return [str(x) for x in v] if isinstance(v, list) else []

        td = _f("technical_depth")
        rq = _f("reasoning_quality")
        ps = _f("problem_solving")
        tt = _f("trade_off_thinking")
        am = _f("answer_maturity")

        overall = _f("overall_llm_score")
        if overall == 0.0:
            overall = round((td + rq + ps + tt + am) / 5, 1)

        return LLMEvaluationScore(
            technical_depth=td,
            technical_feedback=_s("technical_feedback"),
            reasoning_quality=rq,
            reasoning_feedback=_s("reasoning_feedback"),
            problem_solving=ps,
            problem_solving_feedback=_s("problem_solving_feedback"),
            trade_off_thinking=tt,
            trade_off_feedback=_s("trade_off_feedback"),
            answer_maturity=am,
            maturity_feedback=_s("maturity_feedback"),
            overall_llm_score=overall,
            interviewer_summary=_s("interviewer_summary"),
            follow_up_questions=_l("follow_up_questions"),
        )
