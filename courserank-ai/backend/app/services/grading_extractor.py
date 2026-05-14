"""
Extracts grading components and weights from syllabus text and tables.

Strategy (in order of confidence):
  1. Table extraction  — pdfplumber tables that contain % values
  2. Regex line scan   — lines matching "Component .... XX%"
  3. Fallback          — broad regex sweep of the grading section only

Each extracted component is normalized and the total weight is validated.
A confidence score is returned with every result.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.syllabus_parser import ParsedSyllabus


# ── Section-header keywords that signal the grading table is nearby ──────────
GRADING_HEADERS = [
    r"grading\s*scheme",
    r"course\s*grade",
    r"grade\s*breakdown",
    r"grade\s*distribution",
    r"evaluation",
    r"assessments?",
    r"course\s*components?",
    r"marks?\s*distribution",
    r"course\s*work",
    r"grading\s*policy",
    r"grading\s*summary",
    r"how\s*you\s*will\s*be\s*graded",
]

GRADING_HEADER_RE = re.compile(
    r"(?i)(" + "|".join(GRADING_HEADERS) + r")",
)

# Headers that signal the grading section has ended — stop extraction here.
END_OF_GRADING_HEADERS = [
    r"late\s*polic",
    r"late\s*penalt",
    r"missed\s*work",
    r"missed\s*assess",
    r"academic\s*integrity",
    r"academic\s*offence",
    r"plagiarism",
    r"accommodat",
    r"religious\s*observance",
    r"accessibility",
    r"mental\s*health",
    r"course\s*polic",
    r"attendance\s*polic",
    r"learning\s*outcome",
    r"course\s*schedule",
    r"weekly\s*schedule",
    r"important\s*dates",
    r"prerequisite",
    r"textbook",
    r"required\s*reading",
    r"course\s*material",
    r"office\s*hours",
    r"contact\s*information",
    r"to\s*be\s*eligible",
    r"passing\s*grade",
    r"in\s*order\s*to\s*pass",
    r"minimum\s*grade",
]
END_OF_GRADING_RE = re.compile(r"(?i)^\s*(" + "|".join(END_OF_GRADING_HEADERS) + r")")

# Component keywords used to validate / label extracted rows
COMPONENT_KEYWORDS = [
    "assignment", "assignments", "homework", "hw",
    "quiz", "quizzes",
    "midterm", "mid-term", "mid term",
    "test", "tests",
    "final", "final exam", "final examination",
    "lab", "labs", "laboratory",
    "tutorial", "tutorials",
    "participation", "attendance",
    "project", "projects",
    "presentation", "presentations",
    "essay", "report", "reports",
    "exam", "exams", "examination",
    "reading", "readings",
    "group work", "group project",
]

# Words that, if present in a "component name", indicate it's actually a
# pass/fail condition, late penalty clause, or other prose — not a grading row.
DISQUALIFYING_PHRASES = [
    "must receive", "must obtain", "must achieve", "must pass",
    "must score", "must earn",
    "eligible", "weighted average of at least", "in order to",
    "if these conditions", "maximum mark", "pro rated", "prorated",
    "days late", "day late", "submitted", "on time",
    "course grade", "grand total", "overall mark", "overall grade",
    "minimum of", "at least a", "passing grade", "pass mark", "passing mark",
    "students who", "students must", "you must", "you will receive",
    "you need", "need at least", "required to pass", "to pass the",
    "in order to pass",
]

# Date-like patterns that show up in due date schedules
DATE_PATTERNS = [
    re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}", re.IGNORECASE),
    re.compile(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.IGNORECASE),
    re.compile(r"\bweek\s+\d{1,2}\b", re.IGNORECASE),
]

# A single grading component above this weight is almost certainly garbage.
MAX_REASONABLE_WEIGHT = 70.0
# A "component name" longer than this is almost certainly a sentence.
MAX_REASONABLE_NAME_LEN = 50

# Regex that matches a percentage on a line: "30%", "30 %", "(30%)", "30/100"
PCT_RE = re.compile(r"(\d{1,3}(?:\.\d{1,2})?)\s*%")
FRAC_RE = re.compile(r"(\d{1,3})\s*/\s*100\b")  # alternative: "30/100"


@dataclass
class GradingComponentRaw:
    name: str
    weight: float
    source: str  # "table" | "regex" | "fallback"


@dataclass
class ExtractionResult:
    components: List[GradingComponentRaw] = field(default_factory=list)
    confidence_score: float = 0.0
    notes: List[str] = field(default_factory=list)


# ── Public entry point ────────────────────────────────────────────────────────

def extract_grading(syllabus: ParsedSyllabus) -> ExtractionResult:
    result = ExtractionResult()

    # Try table extraction first (highest confidence)
    table_result = _extract_from_tables(syllabus.tables)
    if table_result.components:
        result = table_result
        result.notes.append("Extracted from PDF table.")

    # Fall back to regex on the full text
    if not result.components:
        text_result = _extract_from_text(syllabus.full_text)
        if text_result.components:
            result = text_result

    # Normalise names and merge duplicates
    result.components = _normalize_and_merge(result.components)

    # Recalculate confidence after normalisation
    result.confidence_score = _calculate_confidence(result.components, result.notes)

    return result


# ── Table extraction ──────────────────────────────────────────────────────────

def _extract_from_tables(
    tables: List[List[List[Optional[str]]]],
) -> ExtractionResult:
    components: list[GradingComponentRaw] = []

    for table in tables:
        rows_hit: list[GradingComponentRaw] = []
        for row in table:
            cells = [str(c).strip() if c else "" for c in row]
            combined = " ".join(cells)

            pct = _find_percentage(combined)
            if pct is None or pct <= 0 or pct > MAX_REASONABLE_WEIGHT:
                continue

            # The component name is whichever cell is NOT the number
            name = _best_name_cell(cells, pct)
            if not name:
                continue

            if not _is_valid_component_name(name):
                continue

            rows_hit.append(GradingComponentRaw(name=name, weight=pct, source="table"))

        # Only accept this table if it looks like a grading table (>=2 rows with %)
        if len(rows_hit) >= 2:
            components.extend(rows_hit)

    return ExtractionResult(components=components)


def _best_name_cell(cells: List[str], pct: float) -> str:
    pct_str = str(int(pct)) if pct == int(pct) else str(pct)
    for cell in cells:
        if pct_str in cell and "%" in cell:
            continue  # this is the percentage cell
        if len(cell) > 2 and not re.fullmatch(r"[\d\s%./-]+", cell):
            return cell.strip()
    return ""


# ── Regex / text extraction ───────────────────────────────────────────────────

def _extract_from_text(full_text: str) -> ExtractionResult:
    section = _isolate_grading_section(full_text)
    source = "regex" if section != full_text else "fallback"
    components = _parse_percentage_lines(section, source)
    return ExtractionResult(components=components)


def _isolate_grading_section(text: str) -> str:
    """
    Find the grading section header and return the lines after it, stopping
    at the next major section header (late policy, academic integrity, etc.).
    Capped at 50 lines as a safety net. Falls back to full text if no header.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if GRADING_HEADER_RE.search(line):
            snippet = [line]
            for j in range(i + 1, min(i + 51, len(lines))):
                if END_OF_GRADING_RE.search(lines[j]):
                    break
                snippet.append(lines[j])
            return "\n".join(snippet)
    return text


def _is_valid_component_name(name: str) -> bool:
    """Reject sentence-like fragments, dates, pass/fail conditions, late-penalty rows."""
    if len(name) < 3 or len(name) > MAX_REASONABLE_NAME_LEN:
        return False
    if re.fullmatch(r"[\d\s.]+", name):
        return False
    if re.fullmatch(r"(grand\s+)?total", name.strip(), re.IGNORECASE):
        return False
    lower = name.lower()
    if any(phrase in lower for phrase in DISQUALIFYING_PHRASES):
        return False
    for pat in DATE_PATTERNS:
        if pat.search(name):
            return False
    # Reject sentence-like names (too many words, or ends mid-phrase)
    if len(name.split()) > 6:
        return False
    return True


def _parse_percentage_lines(text: str, source: str) -> List[GradingComponentRaw]:
    components: list[GradingComponentRaw] = []
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        pct = _find_percentage(line)
        if pct is None or pct <= 0 or pct > MAX_REASONABLE_WEIGHT:
            continue

        # Strip the percentage token from the line to get the component name
        name = PCT_RE.sub("", line)
        name = FRAC_RE.sub("", name)
        name = re.sub(r"[\[\]()|:*•·\-]+", " ", name).strip()
        name = re.sub(r"\s{2,}", " ", name)

        if not _is_valid_component_name(name):
            continue

        components.append(GradingComponentRaw(name=name, weight=pct, source=source))

    return components


# ── Normalisation & deduplication ─────────────────────────────────────────────

_NORM_MAP = {
    r"\bhw\b": "Homework",
    r"\bassignments?\b": "Assignments",
    r"\bhomework\b": "Homework",
    r"\bquizzes\b": "Quizzes",
    r"\bquiz\b": "Quiz",
    r"\bmid[\s-]?term\b": "Midterm",
    r"\bfinal\s+exam(?:ination)?\b": "Final Exam",
    r"\bfinal\b(?!\s+exam)": "Final Exam",
    r"\blabs?\b": "Labs",
    r"\blaboratory\b": "Labs",
    r"\btutorials?\b": "Tutorial",
    r"\bparticipation\b": "Participation",
    r"\battendance\b": "Attendance",
    r"\bprojects?\b": "Project",
    r"\bpresentations?\b": "Presentation",
    r"\bessays?\b": "Essay",
    r"\breports?\b": "Report",
    r"(?<!Final\s)\bexams?\b": "Exam",
    r"(?<!Final\s)\bexamination\b": "Exam",
}


def _normalize_name(name: str) -> str:
    cleaned = name.strip().title()
    for pattern, replacement in _NORM_MAP.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _normalize_and_merge(
    components: List[GradingComponentRaw],
) -> List[GradingComponentRaw]:
    seen: dict[str, GradingComponentRaw] = {}
    for c in components:
        norm = _normalize_name(c.name)
        if norm in seen:
            # Keep higher-confidence source; add weights if clearly separate entries
            existing = seen[norm]
            if existing.source == "table" and c.source != "table":
                continue
            # Same name appearing twice → keep one, sum only if weights differ
            if abs(existing.weight - c.weight) > 0.5:
                existing.weight += c.weight
        else:
            seen[norm] = GradingComponentRaw(
                name=norm, weight=c.weight, source=c.source
            )
    return list(seen.values())


# ── Confidence scoring ────────────────────────────────────────────────────────

def _calculate_confidence(
    components: List[GradingComponentRaw],
    notes: List[str],
) -> float:
    if not components:
        return 0.0

    total = sum(c.weight for c in components)
    n = len(components)

    score = 0.0

    # Weight sum close to 100
    deviation = abs(total - 100)
    if deviation <= 1:
        score += 0.40
    elif deviation <= 5:
        score += 0.28
    elif deviation <= 15:
        score += 0.15
    else:
        score += 0.05

    # Number of components is reasonable
    if 3 <= n <= 8:
        score += 0.25
    elif n == 2 or n == 9:
        score += 0.15
    elif n >= 2:
        score += 0.08

    # Source bonus
    sources = {c.source for c in components}
    if "table" in sources:
        score += 0.25
    elif "regex" in sources:
        score += 0.10

    # All components contain a known keyword
    kw_hits = sum(
        1 for c in components
        if any(kw in c.name.lower() for kw in COMPONENT_KEYWORDS)
    )
    score += 0.10 * (kw_hits / n)

    return round(min(score, 1.0), 3)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_percentage(text: str) -> Optional[float]:
    m = PCT_RE.search(text)
    if m:
        return float(m.group(1))
    m = FRAC_RE.search(text)
    if m:
        return float(m.group(1))
    return None
