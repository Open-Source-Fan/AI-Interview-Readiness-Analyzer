
\# 🎯 AI Interview Readiness Analyzer



An AI-powered mock interview platform that generates role-specific interview

questions from a job description, evaluates candidate answers using the STAR

method, content relevance, and communication quality, and produces a detailed

readiness report with actionable feedback.



\## Live Demo



🔗 \[Try it here](#) <!-- add your Streamlit Cloud URL here -->



\## Features



\- \*\*Job description parsing\*\* — extracts role, experience level, required

&#x20; skills, and tech stack using spaCy NER (no API cost)

\- \*\*AI question generation\*\* — produces 10 tailored interview questions

&#x20; (behavioural, technical, situational, culture fit) via Gemini

\- \*\*STAR method scoring\*\* — evaluates each answer for Situation, Task,

&#x20; Action, and Result completeness with evidence quotes

\- \*\*Content relevance scoring\*\* — sentence-transformers cosine similarity

&#x20; (free, local, no API cost)

\- \*\*Communication quality analysis\*\* — reading ease, filler words, passive

&#x20; voice, vocabulary diversity via spaCy + textstat

\- \*\*Personalised feedback\*\* — 2 specific improvement tips per answer

\- \*\*Readiness report dashboard\*\* — overall score gauge, strengths, gaps,

&#x20; per-question breakdown, and practice recommendations



\## Tech Stack



Python · LangChain · Google Gemini · spaCy · sentence-transformers ·

FastAPI · Streamlit · Plotly · pytest · GitHub Actions



\## Architecture

JD Input → JD Parser (spaCy) → Question Generator (Gemini)



→ Mock Interview (Streamlit) → Evaluation Engine



├── STAR Scorer (Gemini)



├── Content Relevance (sentence-transformers)



└── Communication Analyzer (spaCy + textstat)



→ Readiness Report (score, strengths, gaps, recommendations)

\## Running Locally



```bash

git clone https://github.com/Open-Source-Fan/AI-Interview-Readiness-Analyzer.git

cd AI-Interview-Readiness-Analyzer

python -m venv venv

venv\\Scripts\\activate          # Windows

pip install -r requirements.txt

python -m spacy download en\_core\_web\_sm



\# Add your Gemini API key

copy .env.example .env

\# edit .env and add GEMINI\_API\_KEY=your\_key\_here



streamlit run app.py

```



\## Running Tests



```bash

python -m pytest tests/ -v

```



\## Project Structure

src/



jd\_parser.py      — Module 1: job description parsing (spaCy)



question\_gen.py   — Module 2: AI question generation (Gemini)



evaluator.py       — Module 4: STAR/relevance/communication evaluation



schemas.py         — Pydantic data models for the full pipeline



prompts/             — LLM prompt templates



tests/               — pytest test suite



app.py               — Streamlit frontend



\## License



MIT


# AI-Powered Interview Readiness Analyzer 🚀

An AI-powered mock interview platform that helps candidates prepare for technical interviews by analyzing job descriptions, generating role-specific interview questions, evaluating responses, and providing personalized improvement feedback.

The system combines Large Language Models (LLMs) with traditional NLP techniques to provide a structured interview readiness assessment.

---

## Features

### 📄 Job Description Analysis
- Extracts role title, required skills, experience level, and technology stack from raw job descriptions.
- Uses spaCy-based NLP processing without additional API costs.

### 🤖 AI-Based Question Generation
- Generates role-specific interview questions using Google Gemini.
- Supports different question categories:
  - Behavioural
  - Technical
  - Situational
  - Culture fit

### 🧠 Multi-Dimensional Answer Evaluation

Each interview answer is evaluated across multiple dimensions:

#### STAR Method Evaluation (LLM Powered)
Evaluates:
- Situation
- Task
- Action
- Result

Each component receives a score with supporting feedback.

#### Content Relevance Analysis
- Uses sentence-transformers embeddings.
- Calculates similarity between interview questions and candidate responses.
- Runs locally without API cost.

#### Communication Analysis
Evaluates:
- Reading difficulty
- Filler words
- Passive voice usage
- Vocabulary diversity

Powered by spaCy and textstat.

### 💡 Personalized Feedback
- Generates specific improvement suggestions for every answer using Gemini.

### 📊 Readiness Report Dashboard
Provides:
- Overall readiness score (0-100)
- Performance tier
- Strength analysis
- Improvement areas
- Practice recommendations
- Question-wise evaluation breakdown

### 🌐 Interactive Web Application
Built with Streamlit:
- Job description input
- Mock interview workflow
- Real-time progress tracking
- Visual reports using Plotly

---

# Tech Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini |
| LLM Framework | LangChain |
| NLP | spaCy |
| Semantic Similarity | Sentence Transformers |
| Text Analysis | Textstat |
| Data Validation | Pydantic |
| Frontend | Streamlit |
| Visualization | Plotly |
| Testing | Pytest |
| CI/CD | GitHub Actions |

---

# Project Architecture
AI-Interview-Readiness-Analyzer/
│── app.py                 # Streamlit application
│
├── src/
│   ├── schemas.py         # Data models
│   ├── jd_parser.py       # Job description parser
│   ├── question_gen.py    # AI question generation
│   └── evaluator.py       # Answer evaluation engine
│
├── prompts/
│   ├── question_gen.txt
│   ├── star_scorer.txt
│   └── feedback_gen.txt
│
├── tests/
│
├── config.yaml
├── requirements.txt
└── .github/workflows/

# Future Improvements
PDF export for interview reports
FastAPI backend APIs
User authentication
Interview history tracking
Voice-based answers using speech-to-text
Production deployment with cloud infrastructure


