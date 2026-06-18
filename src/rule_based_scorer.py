"""
rule_based_scorer.py — Module 4b: Rule-Based Evaluation

Computes five objective sub-scores from the raw answer text using regex and
keyword matching. Zero API calls, runs in milliseconds. Results are fully
explainable — every score comes with the signals that drove it.

Sub-scores
----------
1. Ownership score        — first-person action language ("I designed", "I led")
2. Impact score           — quantified results (numbers, %, time, money)
3. Skill coverage         — JD skills/tech mentioned in the answer
4. STAR structure         — heuristic detection of each STAR component
5. Word count score       — penalises too-short and too-long answers
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schemas import ParsedJD, Question, RuleBasedScore


# ── Ownership signal patterns ──────────────────────────────────────────────────

_OWNERSHIP_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bI\s+(designed|built|led|created|developed|implemented|architected|"
               r"deployed|wrote|owned|managed|drove|initiated|launched|established|"
               r"configured|optimised|optimized|refactored|migrated|proposed|"
               r"introduced|automated|reduced|improved|increased|fixed|solved|"
               r"identified|decided|chose|selected|defined|delivered)\b", re.IGNORECASE),
    re.compile(r"\bmy\s+(approach|decision|solution|design|idea|contribution|"
               r"implementation|responsibility|initiative)\b", re.IGNORECASE),
    re.compile(r"\bI\s+took\s+(ownership|responsibility|the\s+lead)\b", re.IGNORECASE),
    re.compile(r"\bI\s+was\s+responsible\s+for\b", re.IGNORECASE),
]

# Weak / team-deflecting patterns reduce score
_WEAK_OWNERSHIP_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(the team|we all|everyone|they|someone else)\s+(did|handled|"
               r"built|decided|worked on)\b", re.IGNORECASE),
]


# ── Impact / quantification patterns ──────────────────────────────────────────

_IMPACT_PATTERNS: list[re.Pattern] = [
    # Percentages and multipliers
    re.compile(r"\b\d+(\.\d+)?\s*(%|percent|x\b|times\s+faster|times\s+more|"
               r"times\s+better)\b", re.IGNORECASE),
    # Money
    re.compile(r"\$\s*\d+(\.\d+)?\s*(k|m|million|thousand|billion)?\b", re.IGNORECASE),
    # Time savings
    re.compile(r"\b\d+\s*(hour|minute|day|week|month|second)s?\s+(saved|reduced|"
               r"faster|quicker|improvement)\b", re.IGNORECASE),
    # User / scale metrics
    re.compile(r"\b\d[\d,]*\s*(user|customer|request|transaction|record|"
               r"event|ticket|order|call)s?\b", re.IGNORECASE),
    # "reduced by N", "improved by N"
    re.compile(r"\b(reduced|improved|increased|decreased|cut|boosted|grew|"
               r"saved|scaled)\s+(\w+\s+)*by\s+\d", re.IGNORECASE),
    # "from X to Y"
    re.compile(r"\bfrom\s+\d[\d,]*(\.\d+)?\s*(ms|s|%|k|m)?\s+to\s+\d",
               re.IGNORECASE),
]


# ── STAR heuristic patterns ────────────────────────────────────────────────────

_STAR_PATTERNS: dict[str, list[re.Pattern]] = {
    "Situation": [
        re.compile(r"\b(at the time|back then|we were|our team was|the context|"
                   r"the situation was|we had a|when I was|while working on|"
                   r"in my (previous|current|last) (role|job|company|project))\b",
                   re.IGNORECASE),
        re.compile(r"\b(faced|encountered|noticed|realised|realized|discovered|"
                   r"found that)\b", re.IGNORECASE),
    ],
    "Task": [
        re.compile(r"\b(my goal was|my task was|I was asked to|I needed to|"
                   r"my responsibility was|my objective was|I had to|"
                   r"I was assigned|the challenge was)\b", re.IGNORECASE),
    ],
    "Action": [
        re.compile(r"\bI\s+(started|began|first|then|next|decided|chose|"
                   r"worked on|reached out|set up|wrote|built|deployed|"
                   r"analyzed|analysed|investigated|implemented|designed)\b",
                   re.IGNORECASE),
        re.compile(r"\b(step 1|step 2|first I|then I|after that I|"
                   r"to (do|fix|solve|address) this[,\s]+I)\b", re.IGNORECASE),
    ],
    "Result": [
        re.compile(r"\b(as a result|the result was|this led to|this resulted in|"
                   r"in the end|ultimately|we achieved|the outcome was|"
                   r"which meant|which helped|the impact was|after this|"
                   r"following this)\b", re.IGNORECASE),
        re.compile(r"\b(reduced|improved|increased|saved|fixed|resolved|"
                   r"delivered|shipped|launched|achieved|cut|eliminated)\b",
                   re.IGNORECASE),
    ],
}


# ── Word count scoring curve ───────────────────────────────────────────────────

def _word_count_score(word_count: int) -> tuple[float, str]:
    """
    Ideal answer length is 80–200 words.
    Returns (score 0-10, feedback string).
    """
    if word_count < 30:
        return 2.0, f"Answer is very short ({word_count} words) — aim for at least 80 words."
    if word_count < 60:
        return 5.0, f"Answer is brief ({word_count} words) — add more detail about your specific actions."
    if word_count <= 200:
        return 10.0, f"Good answer length ({word_count} words)."
    if word_count <= 300:
        return 7.0, f"Answer is a little long ({word_count} words) — try to be more concise."
    return 4.0, f"Answer is too long ({word_count} words) — focus on the most impactful points."


# ── Main scorer class ──────────────────────────────────────────────────────────

class RuleBasedScorer:
    """
    Stateless scorer — instantiate once, call .score() for each Q&A pair.
    All methods are pure functions with no side effects.
    """

    def score(
        self,
        answer: str,
        question: "Question",
        parsed_jd: "ParsedJD | None" = None,
    ) -> "RuleBasedScore":
        # Import here to avoid circular import at module load time
        from .schemas import RuleBasedScore

        ownership  = self._score_ownership(answer)
        impact     = self._score_impact(answer)
        skill      = self._score_skill_coverage(answer, question, parsed_jd)
        star       = self._score_star_structure(answer)
        wc_score, wc_fb = _word_count_score(len(answer.split()))

        return RuleBasedScore(
            # Ownership
            ownership_score=ownership["score"],
            ownership_signals=ownership["signals"],
            ownership_feedback=ownership["feedback"],
            # Impact
            impact_score=impact["score"],
            impact_evidence=impact["evidence"],
            impact_feedback=impact["feedback"],
            # Skill coverage
            skill_coverage_pct=skill["coverage_pct"],
            matched_skills=skill["matched"],
            missing_skills=skill["missing"],
            skill_feedback=skill["feedback"],
            # STAR structure
            star_structure_score=star["score"],
            star_hints_found=star["hints"],
            star_feedback=star["feedback"],
            # Word count
            word_count_score=wc_score,
            word_count=len(answer.split()),
            completeness_feedback=wc_fb,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _score_ownership(self, answer: str) -> dict:
        signals: list[str] = []
        for pat in _OWNERSHIP_PATTERNS:
            matches = pat.findall(answer)
            signals.extend(m if isinstance(m, str) else m[0] for m in matches)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_signals: list[str] = []
        for s in signals:
            key = s.lower()
            if key not in seen:
                seen.add(key)
                unique_signals.append(s)

        # Penalty for team-deflection language
        weak_count = sum(
            len(pat.findall(answer)) for pat in _WEAK_OWNERSHIP_PATTERNS
        )

        raw_score = min(len(unique_signals) * 2.0, 10.0) - (weak_count * 1.5)
        score     = round(max(0.0, raw_score), 1)

        if score >= 7.0:
            feedback = "Strong ownership language — clearly describes personal contributions."
        elif score >= 4.0:
            feedback = (
                "Moderate ownership language. Add more first-person action verbs "
                "(e.g. 'I designed', 'I led', 'I implemented')."
            )
        else:
            feedback = (
                "Weak ownership signals. Avoid passive phrasing ('the team did', 'we handled'). "
                "Describe specifically what YOU did."
            )

        return {"score": score, "signals": unique_signals[:8], "feedback": feedback}

    def _score_impact(self, answer: str) -> dict:
        evidence: list[str] = []
        for pat in _IMPACT_PATTERNS:
            for match in pat.finditer(answer):
                # Get a short surrounding snippet for display
                start = max(0, match.start() - 10)
                end   = min(len(answer), match.end() + 20)
                snippet = answer[start:end].strip().replace("\n", " ")
                evidence.append(f"…{snippet}…")

        # Deduplicate snippets
        unique_evidence = list(dict.fromkeys(evidence))[:5]
        count  = len(unique_evidence)
        score  = min(count * 3.5, 10.0)
        score  = round(score, 1)

        if score >= 7.0:
            feedback = "Excellent use of quantified results — numbers make your impact credible."
        elif score >= 4.0:
            feedback = (
                "Some quantification present. Add more numbers: "
                "percentage improvements, time saved, users affected."
            )
        else:
            feedback = (
                "No quantified results found. Interviewers remember numbers — "
                "add at least one metric (e.g. 'reduced latency by 40%', 'saved 2 hours/week')."
            )

        return {"score": score, "evidence": unique_evidence, "feedback": feedback}

    def _score_skill_coverage(
        self,
        answer: str,
        question: "Question",
        parsed_jd: "ParsedJD | None",
    ) -> dict:
        # Collect all keywords to check against
        keywords: list[str] = list(question.ideal_topics)
        if parsed_jd:
            keywords += parsed_jd.required_skills + parsed_jd.tech_stack

        # Deduplicate, lowercase
        unique_kw = list({k.lower() for k in keywords if k.strip()})

        if not unique_kw:
            return {
                "coverage_pct": 50.0,  # neutral when no JD data
                "matched": [],
                "missing": [],
                "feedback": "No JD skills provided — paste a full job description for skill-coverage scoring.",
            }

        answer_lower = answer.lower()
        matched = [kw for kw in unique_kw if re.search(r'\b' + re.escape(kw) + r'\b', answer_lower)]
        missing = [kw for kw in unique_kw if kw not in matched]

        coverage_pct = round(len(matched) / len(unique_kw) * 100, 1)

        if coverage_pct >= 70:
            feedback = f"Strong skill coverage — {len(matched)}/{len(unique_kw)} required skills mentioned."
        elif coverage_pct >= 40:
            top_missing = missing[:3]
            feedback = (
                f"Moderate coverage ({len(matched)}/{len(unique_kw)} skills). "
                f"Consider mentioning: {', '.join(top_missing)}."
            )
        else:
            top_missing = missing[:4]
            feedback = (
                f"Low skill coverage ({len(matched)}/{len(unique_kw)} skills). "
                f"Weave in: {', '.join(top_missing)} where relevant."
            )

        return {
            "coverage_pct": coverage_pct,
            "matched": matched[:10],
            "missing": missing[:10],
            "feedback": feedback,
        }

    def _score_star_structure(self, answer: str) -> dict:
        hints_found: list[str] = []
        component_scores: dict[str, bool] = {}

        for component, patterns in _STAR_PATTERNS.items():
            found = False
            for pat in patterns:
                if pat.search(answer):
                    found = True
                    hints_found.append(f"{component}: signal detected")
                    break
            component_scores[component] = found

        present_count = sum(component_scores.values())
        score         = round(present_count / 4 * 10, 1)

        missing = [c for c, v in component_scores.items() if not v]

        if score >= 8.0:
            feedback = "Clear STAR structure detected — all four components present."
        elif score >= 5.0:
            feedback = (
                f"Partial STAR structure. Missing signals for: {', '.join(missing)}. "
                "Add explicit setup, action steps, and measurable outcomes."
            )
        else:
            feedback = (
                f"Weak STAR structure. Missing: {', '.join(missing)}. "
                "Structure your answer: Situation → Task → Action → Result."
            )

        return {"score": score, "hints": hints_found, "feedback": feedback}
