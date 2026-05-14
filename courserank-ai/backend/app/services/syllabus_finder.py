"""
Auto Syllabus Finder
====================
Finds publicly available syllabus PDFs for Western University courses.

Strategy:
  1. Try known department URL patterns (CS dept posts at predictable paths)
  2. Fall back to DuckDuckGo text search if available
"""
import re
import time
import random
from typing import Optional

import requests

from app.services.syllabus_parser import parse_pdf
from app.services.grading_extractor import extract_grading
from app.services.llm_extractor import extract_grading_llm

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*;q=0.8",
})

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB


# ── Known department syllabus URL patterns ────────────────────────────────────

def _cs_candidate_urls(course_code: str) -> list[str]:
    """Western CS dept posts outlines at csd.uwo.ca/misc/outlines/{year}-{term}/"""
    # Parse course number from "CS 1027" → "1027"
    m = re.match(r"CS\s*(\d+)", course_code, re.IGNORECASE)
    if not m:
        return []
    num = m.group(1)

    urls = []
    current_year = 2026
    for year in range(current_year, current_year - 3, -1):
        for term, label in [("Winter", "W"), ("Fall", "F"), ("Summer", "S")]:
            base = f"https://www.csd.uwo.ca/misc/outlines/{year}-{term}/"
            for suffix in [
                f"CS{num}B.pdf",
                f"CS{num}A.pdf",
                f"CS_{num}B_FW{str(year-1)[2:]}.pdf",
                f"CS_{num}A_FW{str(year-1)[2:]}.pdf",
                f"CS{num}.pdf",
            ]:
                urls.append(base + suffix)
    return urls


def _se_candidate_urls(course_code: str) -> list[str]:
    m = re.match(r"SE\s*(\d+)", course_code, re.IGNORECASE)
    if not m:
        return []
    num = m.group(1)
    urls = []
    for year in range(2026, 2023, -1):
        for term in ["Winter", "Fall"]:
            base = f"https://www.eng.uwo.ca/se/courses/outlines/{year}-{term}/"
            urls.append(base + f"SE{num}.pdf")
    return urls


# ── Generic search via DuckDuckGo HTML (best-effort) ─────────────────────────

def _ddg_search(query: str, max_results: int = 8) -> list[str]:
    from bs4 import BeautifulSoup
    try:
        resp = _SESSION.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []
        for a in soup.select("a.result__url, a.result__a"):
            href = a.get("href", "")
            if href.startswith("http") and href not in urls:
                urls.append(href)
            if len(urls) >= max_results:
                break
        return urls
    except Exception:
        return []


def _search_web(course_code: str, course_name: str) -> list[str]:
    """Try multiple search queries and collect .pdf URLs."""
    queries = [
        f'"{course_code}" syllabus filetype:pdf site:uwo.ca',
        f'"{course_code}" course outline filetype:pdf western university',
        f'"{course_code}" "{course_name}" syllabus filetype:pdf',
    ]
    found = []
    for q in queries:
        results = _ddg_search(q)
        for url in results:
            if url.lower().endswith(".pdf") and url not in found:
                found.append(url)
        if found:
            break
        time.sleep(random.uniform(8.0, 14.0))
    return found


# ── PDF download + parse ──────────────────────────────────────────────────────

def _download_pdf(url: str) -> Optional[bytes]:
    try:
        resp = _SESSION.get(url, timeout=20, stream=True)
        if resp.status_code != 200:
            return None
        content_type = resp.headers.get("Content-Type", "")
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            return None
        data = b""
        for chunk in resp.iter_content(8192):
            data += chunk
            if len(data) > MAX_PDF_BYTES:
                return None
        return data or None
    except Exception:
        return None


def _try_parse(pdf_bytes: bytes) -> Optional[dict]:
    try:
        parsed = parse_pdf(pdf_bytes)
        if not parsed.full_text or len(parsed.full_text) < 150:
            return None

        # Try LLM extraction first (handles messy formatting well)
        result = extract_grading_llm(parsed.full_text)

        # Fall back to regex extractor if LLM unavailable or returned nothing
        if result is None or not result.components:
            result = extract_grading(parsed)

        return {
            "raw_text": parsed.full_text,
            "components": [{"name": c.name, "weight": c.weight} for c in result.components],
            "confidence": result.confidence_score,
        }
    except Exception:
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def find_syllabus(course_code: str, course_name: str) -> Optional[dict]:
    """
    Search for a syllabus PDF for the given course.

    Returns dict with keys: source_url, raw_text, components, confidence
    or None if no usable syllabus found.
    """
    # Step 1: try known department URL patterns
    prefix = course_code.split()[0].upper() if course_code else ""
    pattern_urls: list[str] = []
    if prefix == "CS":
        pattern_urls = _cs_candidate_urls(course_code)
    elif prefix == "SE":
        pattern_urls = _se_candidate_urls(course_code)

    for url in pattern_urls:
        pdf_bytes = _download_pdf(url)
        if not pdf_bytes:
            continue
        result = _try_parse(pdf_bytes)
        if result:
            result["source_url"] = url
            return result
        time.sleep(0.3)

    # Step 2: fall back to web search
    time.sleep(random.uniform(10.0, 18.0))
    web_urls = _search_web(course_code, course_name)
    for url in web_urls:
        pdf_bytes = _download_pdf(url)
        if not pdf_bytes:
            continue
        result = _try_parse(pdf_bytes)
        if result:
            result["source_url"] = url
            return result

    return None
