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

