"""
jd_parser.py — Module 1: JD Parser
Pure spaCy-based extraction. No LLM call, no API cost.

Takes raw job description text and produces a structured ParsedJD object:
role title, experience level, required skills, nice-to-have skills,
tech stack, and key responsibilities.
"""

import re
import spacy

from .schemas import ParsedJD


# ─────────────────────────────────────────
# REFERENCE DATA
# ─────────────────────────────────────────

# Common tech / tool keywords to detect as "tech stack".
# This list is intentionally broad — covers languages, frameworks,
# databases, cloud platforms, and common tools.
TECH_KEYWORDS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "scala", "kotlin", "swift",
    "react", "angular", "vue", "next.js", "django", "flask", "fastapi",
    "spring", "spring boot", "node.js", "express", "rails",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "ci/cd", "git",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "spark", "hadoop", "airflow", "kafka", "rabbitmq",
    "html", "css", "tailwind", "bootstrap", "graphql", "rest", "grpc",
    "linux", "bash", "powershell", "nginx", "apache",
}

# Experience-level signal words and their normalised label.
EXPERIENCE_PATTERNS = [
    (r"\b(senior|sr\.?|lead|principal|staff)\b", "Senior"),
    (r"\b(junior|jr\.?|entry[\s-]level|graduate|fresher)\b", "Junior"),
    (r"\b(mid[\s-]level|intermediate)\b", "Mid"),
    (r"\b(\d+)\+?\s*(?:to\s*\d+\s*)?years?\b", None),  # handled specially below
]

# Phrases that often introduce a responsibilities section.
RESPONSIBILITY_HEADERS = [
    "responsibilities", "what you'll do", "what you will do",
    "key responsibilities", "duties", "role overview", "about the role",
    "your role", "day to day", "day-to-day",
]

# Phrases that often introduce a "nice to have" section.
NICE_TO_HAVE_HEADERS = [
    "nice to have", "preferred", "bonus", "good to have",
    "desirable", "pluses", "plus points", "would be a plus",
]

# Phrases that often introduce a required skills section.
REQUIRED_HEADERS = [
    "requirements", "required skills", "must have", "qualifications",
    "what we're looking for", "what we are looking for", "skills required",
    "minimum qualifications", "you have", "you bring",
]


class JDParser:
    """
    Parses raw job description text into a structured ParsedJD object
    using spaCy NER + rule-based keyword/section matching.

    Usage:
        parser = JDParser()
        parsed = parser.parse(jd_text)
    """

    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    # ─────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ─────────────────────────────────────

    def parse(self, jd_text: str) -> ParsedJD:
        if not jd_text or not jd_text.strip():
            raise ValueError("JD text cannot be empty")

        doc = self.nlp(jd_text)

        role_title       = self._extract_role_title(jd_text, doc)
        experience_level = self._extract_experience_level(jd_text)
        tech_stack        = self._extract_tech_stack(jd_text)

        required_section, nice_section, resp_section = self._split_sections(jd_text)

        required_skills = self._extract_skill_list(required_section, tech_stack)
        nice_to_have    = self._extract_skill_list(nice_section, tech_stack)
        responsibilities = self._extract_bullet_list(resp_section)

        # Fallback: if no skills found in sections, use detected tech stack
        if not required_skills:
            required_skills = sorted(tech_stack)[:8]

        return ParsedJD(
            raw_text=jd_text,
            role_title=role_title,
            experience_level=experience_level,
            required_skills=required_skills,
            nice_to_have=nice_to_have,
            tech_stack=sorted(tech_stack),
            responsibilities=responsibilities,
        )

    # ─────────────────────────────────────
    # ROLE TITLE EXTRACTION
    # ─────────────────────────────────────

    def _extract_role_title(self, text: str, doc) -> str:
        """
        Heuristic: the role title is usually in the first 1-2 lines,
        often after words like 'hiring', 'seeking', 'looking for', or
        is simply the first capitalised noun phrase.
        """
        first_lines = "\n".join(text.strip().splitlines()[:3])

        # Pattern: "hiring a/an <Title>" or "looking for a/an <Title>"
        patterns = [
            r"(?:hiring|seeking|looking for)\s+(?:an?\s+)?([A-Z][A-Za-z0-9\s/+\-]{2,50})",
            r"^([A-Z][A-Za-z0-9\s/+\-]{2,50})\s*$",  # title on its own line
            r"Job Title[:\-]\s*([A-Za-z0-9\s/+\-]{2,50})",
            r"Position[:\-]\s*([A-Za-z0-9\s/+\-]{2,50})",
            r"Role[:\-]\s*([A-Za-z0-9\s/+\-]{2,50})",
        ]
        for pattern in patterns:
            match = re.search(pattern, first_lines, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                title = re.split(r"\bwith\b|\bwho\b|\.", title)[0].strip()
                title = title.rstrip(",.;: ")
                if 2 <= len(title) <= 60:
                    return title

        # Fallback: first noun chunk with a capital letter from spaCy
        for chunk in doc.noun_chunks:
            if chunk.text[0].isupper() and len(chunk.text) > 3:
                return chunk.text.strip()

        return "Unspecified Role"

    # ─────────────────────────────────────
    # EXPERIENCE LEVEL EXTRACTION
    # ─────────────────────────────────────

    def _extract_experience_level(self, text: str) -> str:
        lower = text.lower()

        # Check explicit seniority words first
        if re.search(r"\b(senior|sr\.?|lead|principal|staff)\b", lower):
            return "Senior"
        if re.search(r"\b(junior|jr\.?|entry[\s-]level|graduate|fresher|intern)\b", lower):
            return "Junior"
        if re.search(r"\b(mid[\s-]level|intermediate)\b", lower):
            return "Mid"

        # Check for "X+ years" patterns
        year_match = re.search(r"(\d+)\+?\s*(?:to\s*\d+\s*)?\+?\s*years?", lower)
        if year_match:
            years = int(year_match.group(1))
            if years >= 6:
                return "Senior"
            elif years >= 3:
                return "Mid"
            else:
                return "Junior"

        return "Mid"  # sensible default

    # ─────────────────────────────────────
    # TECH STACK EXTRACTION
    # ─────────────────────────────────────

    def _extract_tech_stack(self, text: str) -> set[str]:
        lower = text.lower()
        found = set()
        for keyword in TECH_KEYWORDS:
            # Word-boundary match to avoid partial matches (e.g. "go" inside "going")
            pattern = r"(?<![a-zA-Z0-9])" + re.escape(keyword) + r"(?![a-zA-Z0-9])"
            if re.search(pattern, lower):
                found.add(keyword.title() if len(keyword) > 3 else keyword.upper())
        return found

    # ─────────────────────────────────────
    # SECTION SPLITTING
    # ─────────────────────────────────────

    def _split_sections(self, text: str) -> tuple[str, str, str]:
        """
        Splits the JD into (required_section, nice_to_have_section, responsibilities_section)
        based on common section header phrases. Returns empty strings for sections not found.
        """
        lower = text.lower()
        lines = text.splitlines()
        lower_lines = lower.splitlines()

        def find_section(headers: list[str]) -> str:
            for i, line in enumerate(lower_lines):
                for header in headers:
                    if header in line and len(line.strip()) < 80:
                        # Section starts after this line, ends at next header-like line
                        section_lines = []
                        for j in range(i + 1, len(lines)):
                            next_lower = lower_lines[j].strip()
                            # Stop if we hit another known header
                            if any(h in next_lower for h in
                                   RESPONSIBILITY_HEADERS + NICE_TO_HAVE_HEADERS + REQUIRED_HEADERS) \
                                    and len(next_lower) < 80:
                                break
                            section_lines.append(lines[j])
                        return "\n".join(section_lines)
            return ""

        required_section = find_section(REQUIRED_HEADERS)
        nice_section      = find_section(NICE_TO_HAVE_HEADERS)
        resp_section      = find_section(RESPONSIBILITY_HEADERS)

        return required_section, nice_section, resp_section

    # ─────────────────────────────────────
    # LIST EXTRACTION HELPERS
    # ─────────────────────────────────────

    def _extract_bullet_list(self, section_text: str, max_items: int = 10) -> list[str]:
        """Extracts bullet-point or line-based items from a section."""
        if not section_text.strip():
            return []

        items = []
        for line in section_text.splitlines():
            cleaned = re.sub(r"^[\s\-\*•●▪◦‣·]+", "", line).strip()
            cleaned = cleaned.rstrip(",.;")
            if 3 <= len(cleaned) <= 200:
                items.append(cleaned)
        return items[:max_items]

    def _extract_skill_list(self, section_text: str, tech_stack: set[str], max_items: int = 12) -> list[str]:
        """
        Extracts skill-like items from a section. Each bullet/line is treated
        as a skill if reasonably short, otherwise tech keywords within the
        line are extracted individually.
        """
        if not section_text.strip():
            return []

        skills = []
        for line in section_text.splitlines():
            cleaned = re.sub(r"^[\s\-\*•●▪◦‣·]+", "", line).strip().rstrip(",.;")
            if not cleaned:
                continue

            # Short lines are likely standalone skills
            if len(cleaned) <= 60:
                skills.append(cleaned)
            else:
                # Long line: pull out any tech keywords mentioned in it
                lower_line = cleaned.lower()
                for keyword in tech_stack:
                    if keyword.lower() in lower_line and keyword not in skills:
                        skills.append(keyword)

        # De-duplicate while preserving order
        seen = set()
        unique = []
        for s in skills:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique.append(s)

        return unique[:max_items]
