"""
Department Index Scraper
========================
Fetches each department's course-outlines index page once, extracts ALL PDF
links, matches them to DB courses by course number, then downloads + parses
each PDF.  Much faster than the per-course agent loop.
"""
import re
import time
import random
from typing import Optional
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup

from app.services.syllabus_finder import _download_pdf, _try_parse

# Module-level cache: scrape each dept's index pages only once per process
_DEPT_CACHE: dict[str, dict[str, str]] = {}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── Department index pages ────────────────────────────────────────────────────

DEPT_INDEX_PAGES = {
    "CS": [
        "https://www.csd.uwo.ca/misc/outlines/2026-Winter/",
        "https://www.csd.uwo.ca/misc/outlines/2025-Fall/",
        "https://www.csd.uwo.ca/misc/outlines/2025-Winter/",
        "https://www.csd.uwo.ca/misc/outlines/2024-Fall/",
        "https://www.csd.uwo.ca/undergraduate/current/courses/course_outlines_archive.html",
    ],
    "SE": [
        "https://www.eng.uwo.ca/se/courses/outlines/2026-Winter/",
        "https://www.eng.uwo.ca/se/courses/outlines/2025-Fall/",
        "https://www.eng.uwo.ca/se/courses/outlines/2025-Winter/",
        "https://www.eng.uwo.ca/se/courses/outlines/2024-Fall/",
    ],
    "ECE": [
        "https://www.eng.uwo.ca/electrical/undergraduate/",
    ],
    "MATH": [
        "https://www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/2026/",
        "https://www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/2025/",
        "https://www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/2024/",
    ],
    "CALC": [
        "https://www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/2026/",
        "https://www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/2025/",
        "https://www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/2024/",
    ],
    "APPLMATH": [
        "https://www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/2026/",
        "https://www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/2025/",
    ],
    "STATS": [
        "https://www.uwo.ca/stats/undergraduate/course-outlines/20252026/",
        "https://www.uwo.ca/stats/undergraduate/course-outlines/20242025/",
        "https://www.uwo.ca/stats/undergraduate/course-outlines/20232024/",
    ],
    "DATASCI": [
        "https://www.uwo.ca/stats/undergraduate/course-outlines/20252026/",
        "https://www.uwo.ca/stats/undergraduate/course-outlines/20242025/",
    ],
    "PHYSICS": [
        "https://physics.uwo.ca/pdfs/undergraduate/outlines_25_26/",
        "https://physics.uwo.ca/pdfs/undergraduate/outlines_24_25/",
        "https://physics.uwo.ca/pdfs/undergraduate/outlines_23_24/",
    ],
}


def _fetch_pdf_links(page_url: str) -> list[dict]:
    """Fetch a page and return all PDF links found on it."""
    try:
        resp = requests.get(page_url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" in href.lower():
                full_url = href if href.startswith("http") else urljoin(page_url, href)
                links.append({
                    "url": full_url,
                    "text": a.get_text(strip=True)[:120],
                })
        return links
    except Exception:
        return []


def _extract_course_num(url: str, text: str) -> Optional[str]:
    """Extract a 4-digit course number (1000-4999) from a PDF URL or link text.
    Priority: letter-prefixed numbers (CS1026, Math-1229, Phys 1101) to avoid
    matching year numbers (2025, 2026) that appear in directory paths."""
    filename = unquote(url.split("/")[-1])
    # Pass 1: look for letter immediately before the number (with optional separator)
    # Handles: CS_1026A, Math-1229, AM-4615, Phys 1101, CALC1301
    for target in [filename, text]:
        for m in re.finditer(r"[A-Za-z][-_.\s]?(\d{4})(?!\d)", target):
            num = int(m.group(1))
            if 1000 <= num <= 4999:
                return str(num)
    # Pass 2: any standalone 4-digit number that isn't a calendar year
    for target in [filename, text, url]:
        for m in re.finditer(r"(?<!\d)(\d{4})(?!\d)", target):
            num = int(m.group(1))
            if 1000 <= num <= 4999 and not (2019 <= num <= 2030):
                return str(num)
    return None


def scrape_dept_index(dept: str) -> dict[str, str]:
    """
    Fetch all course outline index pages for a department.
    Returns {course_number: pdf_url} mapping (most recent year wins).
    Results are cached in-process so each dept is only fetched once.
    """
    dept = dept.upper()
    if dept in _DEPT_CACHE:
        return _DEPT_CACHE[dept]

    index_pages = DEPT_INDEX_PAGES.get(dept, [])
    found: dict[str, str] = {}

    for page_url in index_pages:
        links = _fetch_pdf_links(page_url)
        for link in links:
            num = _extract_course_num(link["url"], link["text"])
            if num and num not in found:
                found[num] = link["url"]
        time.sleep(random.uniform(1, 2))

    _DEPT_CACHE[dept] = found
    return found


def find_syllabus_from_index(course_code: str, course_name: str) -> Optional[dict]:
    """
    Try to find a syllabus by scraping the department's index page.
    Returns same dict as find_syllabus(): {source_url, raw_text, components, confidence}
    """
    parts = course_code.split()
    if len(parts) < 2:
        return None
    dept = parts[0].upper()
    num = parts[1]

    if dept not in DEPT_INDEX_PAGES:
        return None

    course_map = scrape_dept_index(dept)
    pdf_url = course_map.get(num)
    if not pdf_url:
        return None

    pdf_bytes = _download_pdf(pdf_url)
    if not pdf_bytes:
        return None

    result = _try_parse(pdf_bytes)
    if result:
        result["source_url"] = pdf_url
    return result
