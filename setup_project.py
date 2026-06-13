import os

# Run this file from INSIDE your interview_analyzer folder
# python setup_project.py

base = os.getcwd()

# ── Folder structure ──────────────────────────────────────
folders = [
    "src",
    "prompts",
    "tests",
    ".github/workflows",
]
for folder in folders:
    os.makedirs(os.path.join(base, folder), exist_ok=True)
    print(f"✓ Created folder: {folder}")

# ── Files to create ───────────────────────────────────────
files = {

    # Empty init file — makes src/ a Python package
    "src/__init__.py": "",

    # Your .env template — copy this to .env and add your key
    ".env.example": "OPENAI_API_KEY=sk-your-key-here\n",

    # .env — actual secrets file (you fill this in)
    ".env": "OPENAI_API_KEY=sk-your-key-here\n",

    # Git ignore — stops .env and junk from being uploaded
    ".gitignore": """\
.env
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
*.egg-info/
dist/
.venv/
venv/
htmlcov/
.coverage
""",

    # GitHub Actions CI workflow
    ".github/workflows/ci.yml": """\
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m spacy download en_core_web_sm

      - name: Lint with ruff
        run: ruff check src/ tests/

      - name: Run tests with coverage
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=75
""",

    # Smoke test — run this to verify your setup works
    "test_run.py": """\
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

print("Testing LangChain + OpenAI connection...")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = PromptTemplate.from_template(
    "Generate 2 behavioural interview questions for a {role} role. Return as a numbered list."
)
chain = prompt | llm
result = chain.invoke({"role": "Python backend engineer"})
print("\\nSUCCESS — Here are your test questions:")
print(result.content)
""",

}

for filepath, content in files.items():
    full_path = os.path.join(base, filepath)
    if os.path.exists(full_path):
        print(f"  (already exists, skipping): {filepath}")
        continue
    with open(full_path, "w") as f:
        f.write(content)
    print(f"✓ Created: {filepath}")

print("\n✅ All done! Your project structure is ready.")
print("\nNext steps:")
print("  1. Open .env and replace sk-your-key-here with your real OpenAI API key")
print("  2. Run:  pip install -r requirements.txt")
print("  3. Run:  python -m spacy download en_core_web_sm")
print("  4. Run:  pytest tests/ -v")
print("  5. Run:  python test_run.py")