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
    """Western CS dept posts outlines at csd.uwo.ca/misc/outlines/{year}-{term}/
    FW code = last 2 digits of the FALL year (Fall 2025 and Winter 2026 both use FW25).
    """
    m = re.match(r"CS\s*(\d+)", course_code, re.IGNORECASE)
    if not m:
        return []
    num = m.group(1)

    urls = []
    current_year = 2026
    for year in range(current_year, current_year - 3, -1):
        # Winter belongs to the previous fall's academic year
        for term, fw_code in [("Winter", str(year - 1)[2:]), ("Fall", str(year)[2:])]:
            base = f"https://www.csd.uwo.ca/misc/outlines/{year}-{term}/"
            for suffix in [
                f"CS_{num}A_FW{fw_code}.pdf",
                f"CS_{num}B_FW{fw_code}.pdf",
                f"CS_{num}Y_FW{fw_code}.pdf",
                f"CS{num}A.pdf",
                f"CS{num}B.pdf",
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


def _math_candidate_urls(course_code: str) -> list[str]:
    """
    Western Math dept posts outlines at:
    math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/{year}/
    Filename pattern: Math-{num}-Course-Outline-{term}-{year}.pdf
    Covers MATH, CALC, APPLMATH (STATS has its own site).
    """
    m = re.match(r"(MATH|CALC|APPLMATH)\s*(\d+)", course_code, re.IGNORECASE)
    if not m:
        return []
    prefix = m.group(1).capitalize()
    num = m.group(2)
    base_url = "https://www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/"
    urls = []
    for year in range(2026, 2020, -1):
        for term in ["Fall", "Winter", "Summer"]:
            urls.append(f"{base_url}{year}/{prefix}-{num}-Course-Outline-{term}-{year}.pdf")
    return urls


def _stats_candidate_urls(course_code: str) -> list[str]:
    """
    Western Stats dept posts outlines at:
    uwo.ca/stats/undergraduate/course-outlines/{academicyear}/
    STATS courses use SS prefix, DATASCI use DS prefix.
    2025-26 format: SS{num}{section}_1259.pdf
    """
    m = re.match(r"(STATS|DATASCI)\s*(\d+)", course_code, re.IGNORECASE)
    if not m:
        return []
    prefix_map = {"STATS": "SS", "DATASCI": "DS"}
    prefix = prefix_map[m.group(1).upper()]
    num = m.group(2)
    base = "https://www.uwo.ca/stats/undergraduate/course-outlines/"
    urls = []
    for year_folder, suffix in [("20252026", "_1259"), ("20242025", ""), ("20232024", "")]:
        for section in ["A", "B", ""]:
            urls.append(f"{base}{year_folder}/{prefix}{num}{section}{suffix}.pdf")
    return urls


def _physics_candidate_urls(course_code: str) -> list[str]:
    """
    Western Physics dept posts outlines at:
    physics.uwo.ca/pdfs/undergraduate/outlines_{yy}_{yy}/
    Most common pattern: Phys {num}.pdf (URL-encoded space as %20)
    """
    m = re.match(r"PHYSICS\s*(\d+)", course_code, re.IGNORECASE)
    if not m:
        return []
    num = m.group(1)
    base = "https://physics.uwo.ca/pdfs/undergraduate/"
    urls = []
    for year_folder in ["outlines_25_26", "outlines_24_25", "outlines_23_24"]:
        urls.append(f"{base}{year_folder}/Phys%20{num}.pdf")
        urls.append(f"{base}{year_folder}/Phys{num}.pdf")
    return urls


def _ece_candidate_urls(course_code: str) -> list[str]:
    """
    Western ECE dept posts outlines at:
    eng.uwo.ca/electrical/undergraduate/
    2025 pattern: ECE-{num}{section}_{term}[-_]{year}[-_]Website[-_]Version.pdf
    2023-24 pattern: ECE-{num}{section}-{year}-{year}_approved.pdf
    Tries both underscore and dash variants plus section letters.
    """
    m = re.match(r"ECE\s*(\d+)", course_code, re.IGNORECASE)
    if not m:
        return []
    num = m.group(1)
    base = "https://www.eng.uwo.ca/electrical/undergraduate/"
    urls = []
    for section in ["A", "B", ""]:
        # 2025-26 variants (two separator styles seen in the wild)
        urls.append(f"{base}ECE-{num}{section}_Fall_2025_Website_Version.pdf")
        urls.append(f"{base}ECE-{num}{section}_Fall-2025-Website-Version.pdf")
        urls.append(f"{base}ECE-{num}{section}_Winter_2026_Website_Version.pdf")
        urls.append(f"{base}ECE-{num}{section}_Winter-2026-Website-Version.pdf")
        # 2024-25 variants
        urls.append(f"{base}ECE-{num}{section}-2024-25.pdf")
        urls.append(f"{base}ECE-{num}{section}_2024-25.pdf")
        # 2023-24 variants
        urls.append(f"{base}ECE-{num}{section}-2023-24_approved.pdf")
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
    elif prefix in ("MATH", "CALC", "APPLMATH"):
        pattern_urls = _math_candidate_urls(course_code)
    elif prefix in ("STATS", "DATASCI"):
        pattern_urls = _stats_candidate_urls(course_code)
    elif prefix == "PHYSICS":
        pattern_urls = _physics_candidate_urls(course_code)
    elif prefix == "ECE":
        pattern_urls = _ece_candidate_urls(course_code)

    for url in pattern_urls:
        pdf_bytes = _download_pdf(url)
        if not pdf_bytes:
            continue
        result = _try_parse(pdf_bytes)
        if result:
            result["source_url"] = url
            return result
        time.sleep(0.3)

    # Step 2: DuckDuckGo search for direct .pdf links
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

    # Step 3: Claude agent — searches the web and navigates pages to find the PDF
    from app.services.syllabus_agent import find_syllabus_agent
    agent_url = find_syllabus_agent(course_code, course_name)
    if agent_url:
        pdf_bytes = _download_pdf(agent_url)
        if pdf_bytes:
            result = _try_parse(pdf_bytes)
            if result:
                result["source_url"] = agent_url
                return result

    return None
