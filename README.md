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

