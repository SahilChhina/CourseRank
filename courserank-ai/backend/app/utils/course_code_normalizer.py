import re


def normalize_course_code(raw: str) -> str:
    """Normalize user input to standard format e.g. 'cs2210' -> 'CS 2210'."""
    cleaned = raw.strip().upper()
    # Insert space between letters and digits if missing: CS2210 -> CS 2210
    normalized = re.sub(r"([A-Z]+)(\d+)", r"\1 \2", cleaned)
    return normalized


def build_search_terms(query: str) -> list[str]:
    """Return a list of search variants for a query string."""
    q = query.strip()
    terms = [q, normalize_course_code(q)]
    return list(set(terms))
