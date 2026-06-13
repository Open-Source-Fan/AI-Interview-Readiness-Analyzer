"""
demo_pipeline.py — End-to-end demo of the full Interview Readiness Analyzer pipeline.

Run this to see: raw JD text -> ParsedJD -> QuestionBank -> (sample answer) -> Evaluation -> Report

Usage:
    venv\\Scripts\\python.exe demo_pipeline.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

from src.jd_parser import JDParser
from src.question_gen import QuestionGenerator
from src.evaluator import EvaluationEngine
from src.schemas import QAPair, ReadinessReport


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

# A sample answer to test evaluation on
SAMPLE_ANSWER = (
    "At my previous company, our checkout API was timing out under heavy load "
    "during a big sale event. I was responsible for figuring out why. I profiled "
    "the database queries and found we were running an unindexed query on every "
    "request. I added a composite index and introduced a Redis cache for product "
    "pricing data. After deploying the fix, average response time dropped from "
    "1200ms to 80ms and we had zero timeouts during the next sale."
)


def main():
    print("=" * 70)
    print("STEP 1: Parsing job description...")
    print("=" * 70)
    parser = JDParser()
    parsed_jd = parser.parse(SAMPLE_JD)

    print(f"Role title:        {parsed_jd.role_title}")
    print(f"Experience level:  {parsed_jd.experience_level}")
    print(f"Required skills:   {parsed_jd.required_skills}")
    print(f"Nice to have:      {parsed_jd.nice_to_have}")
    print(f"Tech stack:        {parsed_jd.tech_stack}")
    print(f"Responsibilities:  {parsed_jd.responsibilities}")

    print()
    print("=" * 70)
    print("STEP 2: Generating interview questions (calls Gemini)...")
    print("=" * 70)
    qgen = QuestionGenerator()  # uses GEMINI_API_KEY from .env
    bank = qgen.generate(parsed_jd)

    for q in bank.questions:
        print(f"[{q.id}] ({q.type.value}/{q.difficulty.value}) {q.text}")

    print()
    print("=" * 70)
    print("STEP 3: Evaluating a sample answer to Q01 (calls Gemini)...")
    print("=" * 70)

    first_question = bank.questions[0]
    print(f"Question: {first_question.text}")
    print(f"Answer:   {SAMPLE_ANSWER[:80]}...")
    print()

    qa_pair = QAPair(question=first_question, answer=SAMPLE_ANSWER)

    engine = EvaluationEngine()  # uses GEMINI_API_KEY from .env
    evaluation = engine.evaluate(qa_pair)

    print(f"STAR scores:")
    print(f"  Situation: {evaluation.star_score.situation_score}/10 - {evaluation.star_score.situation_evidence}")
    print(f"  Task:      {evaluation.star_score.task_score}/10 - {evaluation.star_score.task_evidence}")
    print(f"  Action:    {evaluation.star_score.action_score}/10 - {evaluation.star_score.action_evidence}")
    print(f"  Result:    {evaluation.star_score.result_score}/10 - {evaluation.star_score.result_evidence}")
    print(f"  STAR total: {evaluation.star_score.total}/10")
    print()
    print(f"Content relevance: {evaluation.content_relevance}")
    print(f"Communication score: {evaluation.communication.score}/10")
    print(f"  Reading ease:        {evaluation.communication.reading_ease}")
    print(f"  Filler words:        {evaluation.communication.filler_word_count}")
    print(f"  Passive voice %:     {evaluation.communication.passive_voice_pct}")
    print()
    print(f"COMPOSITE SCORE: {evaluation.composite_score}/100")
    print(f"TIER: {evaluation.tier.value}")
    print()
    print("Improvement tips:")
    for tip in evaluation.improvement_tips:
        print(f"  - {tip}")

    print()
    print("=" * 70)
    print("STEP 4: Building readiness report...")
    print("=" * 70)

    report = ReadinessReport.from_evaluations([evaluation], parsed_jd, candidate_name="Demo User")
    print(f"Overall score: {report.overall_score}/100")
    print(f"Overall tier:  {report.overall_tier.value}")

    print()
    print("PIPELINE COMPLETE — all 4 stages ran successfully.")


if __name__ == "__main__":
    main()
