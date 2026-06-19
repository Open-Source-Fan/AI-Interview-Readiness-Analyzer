# 🎯 AI Interview Readiness Analyzer

![CI](https://github.com/Open-Source-Fan/AI-Interview-Readiness-Analyzer/actions/workflows/ci.yml/badge.svg)

An AI-powered mock interview platform that generates role-specific questions from a job description, evaluates candidate answers using a **3-layer hybrid evaluation engine**, and produces a downloadable readiness report with explainable scores and actionable feedback.

## 🔗 Live Demo

**[Try it here → https://ai-interview-readiness-analyzer-c5hnyjdvusww9syf2gykt5.streamlit.app/)**
*(replace with your actual Streamlit Cloud URL)*

---

## ✨ What It Does

1. **Paste a job description** — extracts role, experience level, required skills, and tech stack using spaCy (no API cost)
2. **Generate tailored questions** — Gemini produces up to 10 role-specific questions across behavioural, technical, situational, and culture-fit categories
3. **Answer at your own pace** — one question at a time with STAR method tips
4. **Get a 4-section hybrid evaluation** — every score is explained, not just a number
5. **Download a PDF report** — full breakdown with AI interviewer notes, objective metrics, and improvement tips

---

## 🧠 Hybrid Evaluation Engine

Most interview tools give you a single opaque LLM score. This platform uses three independent evaluation tracks:

### 1. 🤖 AI Interviewer Assessment (Gemini)
Gemini acts as a senior technical interviewer and scores:
- **Technical Depth** — does the answer show real hands-on knowledge?
- **Reasoning Quality** — does the candidate explain *why*, not just *what*?
- **Problem Solving** — structured thinking and constraint awareness
- **Trade-off Thinking** — awareness of alternatives and their downsides
- **Answer Maturity** — ownership, initiative, system-level thinking

Each dimension includes a 1–2 sentence justification.

### 2. 📊 Objective Rule-Based Metrics (Pure Python)
Deterministic signals computed in milliseconds, zero API cost:
- **Ownership score** — detects first-person action language ("I designed", "I led")
- **Impact score** — finds quantified results (%, numbers, time saved, cost reduced)
- **Skill coverage** — compares answer against JD required skills and tech stack
- **STAR structure** — heuristic detection of all four STAR components
- **Answer completeness** — word count quality curve

### 3. 🗣️ Communication Analysis (spaCy + textstat)
- Reading ease (Flesch score)
- Filler word count
- Passive voice ratio
- Vocabulary diversity

### Final Score Formula
```
Composite Score =
  LLM Assessment  × 40%  (qualitative judgment)
  Rule-Based      × 35%  (objective, reproducible)
  Communication   × 25%  (clarity of expression)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM & orchestration | Google Gemini, LangChain |
| NLP | spaCy, textstat |
| Semantic similarity | sentence-transformers |
| Data validation | Pydantic |
| Frontend | Streamlit, Plotly |
| PDF generation | reportlab |
| Testing | pytest |
| CI/CD | GitHub Actions |
| Deployment | Streamlit Cloud |

---

## 🚀 Running Locally

```bash
git clone https://github.com/Open-Source-Fan/AI-Interview-Readiness-Analyzer.git
cd AI-Interview-Readiness-Analyzer

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

# Add your Gemini API key
copy .env.example .env
# edit .env → GEMINI_API_KEY=your_key_here

streamlit run app.py
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

28 tests, all free (no API calls required). CI runs on every push to `main`.

---

## 📁 Project Structure

```
AI-Interview-Readiness-Analyzer/
│
├── app.py                        # Streamlit frontend (3-step UI)
│
├── src/
│   ├── schemas.py                # All Pydantic data models
│   ├── jd_parser.py              # Module 1: JD parsing (spaCy)
│   ├── question_gen.py           # Module 2: Question generation (Gemini)
│   ├── evaluator.py              # Module 4: Hybrid evaluation engine
│   ├── rule_based_scorer.py      # Deterministic rule-based scoring
│   ├── llm_evaluator.py          # LLM interviewer assessment
│   └── report_gen.py             # Module 5: PDF report generation
│
├── prompts/
│   ├── question_gen.txt          # Question generation prompt
│   ├── star_scorer.txt           # STAR evaluation prompt
│   ├── feedback_gen.txt          # Improvement tips prompt
│   └── interviewer_eval.txt      # Senior interviewer persona prompt
│
├── tests/
│   ├── test_schemas.py           # 13 schema tests
│   ├── test_jd_parser.py         # 11 JD parser tests
│   ├── test_question_gen.py      # 7 question gen tests (FakeLLM)
│   └── test_rule_based_scorer.py # 15 rule-based scorer tests
│
├── config.yaml                   # Scoring weights and thresholds
├── requirements.txt
└── .github/workflows/ci.yml      # GitHub Actions CI
```

---

## 🏗️ Architecture

```
Job Description
      │
      ▼
  JD Parser (spaCy)
  → role, skills, experience, tech stack
      │
      ▼
  Question Generator (Gemini)
  → up to 10 role-specific questions
      │
      ▼
  Mock Interview (Streamlit)
  → candidate answers, one at a time
      │
      ▼
  Evaluation Engine
  ├── LLM Evaluator (Gemini)      → depth, reasoning, maturity
  ├── Rule-Based Scorer (Python)  → ownership, impact, skill coverage
  └── Communication Evaluator     → clarity, filler words, reading ease
      │
      ▼
  Readiness Report
  → 4-section explainable report + PDF download
```

---

## 📄 License

MIT
