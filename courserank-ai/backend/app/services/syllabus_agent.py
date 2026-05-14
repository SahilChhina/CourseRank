"""
Agentic syllabus finder.
Uses Claude with tool use to search the web and locate a syllabus PDF
for courses where direct URL patterns returned nothing.
"""
import json
import os
import random
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

MAX_TURNS = 8
MODEL = "claude-haiku-4-5"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

_TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Search the web for a course syllabus. Returns titles, URLs, and snippets. "
            "Use focused queries like 'CS 3120 Western University course outline 2025 filetype:pdf'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": (
            "Fetch a web page and return its text plus any PDF links on the page. "
            "Use this to browse department course pages looking for syllabus PDF links."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"}
            },
            "required": ["url"],
        },
    },
    {
        "name": "found_pdf",
        "description": (
            "Call this when you have found a direct .pdf URL that is the course syllabus/outline. "
            "This ends the search immediately."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Direct URL to the PDF"},
            },
            "required": ["url"],
        },
    },
]

_SYSTEM = """You are a research agent finding publicly available course syllabuses (course outlines) for Western University (Canada).

Goal: find a DIRECT URL to a PDF course syllabus/outline for the given course.

Strategy:
1. Search for the course using web_search with targeted queries
2. Visit promising department pages with fetch_page to find .pdf links
3. When you find a direct .pdf link for the course outline, call found_pdf immediately

Rules:
- Focus on uwo.ca domains
- Prioritise recent years (2023–2026)
- A course outline / syllabus is what you want — not a textbook or reading list
- If you cannot find a PDF after 3–4 searches, stop — do not invent URLs
- Call found_pdf as soon as you are confident you have the right PDF"""


def _ddg_search(query: str) -> list[dict]:
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers=_HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for r in soup.select(".result")[:8]:
            title = (r.select_one(".result__title") or r.select_one("h2") or "")
            url_el = r.select_one(".result__url")
            snippet_el = r.select_one(".result__snippet")
            url = url_el.get_text(strip=True) if url_el else ""
            if url and not url.startswith("http"):
                url = "https://" + url
            results.append({
                "title": title.get_text(strip=True) if hasattr(title, "get_text") else str(title),
                "url": url,
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })
        return [r for r in results if r["url"]]
    except Exception:
        return []


def _fetch_page(url: str) -> dict:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}", "pdf_links": []}
        soup = BeautifulSoup(resp.text, "html.parser")
        pdf_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" in href.lower():
                full = href if href.startswith("http") else urljoin(url, href)
                pdf_links.append({"text": a.get_text(strip=True)[:120], "url": full})
        text = soup.get_text(separator="\n", strip=True)[:3000]
        return {"text": text, "pdf_links": pdf_links[:20]}
    except Exception as e:
        return {"error": str(e), "pdf_links": []}


def _run_tool(name: str, inputs: dict) -> str:
    if name == "web_search":
        results = _ddg_search(inputs["query"])
        time.sleep(random.uniform(4, 8))
        return json.dumps(results or [{"note": "No results"}])
    if name == "fetch_page":
        result = _fetch_page(inputs["url"])
        time.sleep(random.uniform(1, 2))
        return json.dumps(result)
    return "ok"


def find_syllabus_agent(course_code: str, course_name: str) -> Optional[str]:
    """
    Use Claude with tool use to find a syllabus PDF URL.
    Returns a direct PDF URL or None if not found.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = Anthropic(api_key=api_key)
    messages = [
        {
            "role": "user",
            "content": (
                f"Find the course syllabus PDF for: {course_code} — {course_name} "
                f"at Western University, Ontario, Canada."
            ),
        }
    ]

    for _ in range(MAX_TURNS):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=_SYSTEM,
                tools=_TOOLS,
                messages=messages,
            )
        except Exception as e:
            print(f"[syllabus_agent] API error for {course_code}: {e}")
            return None

        # Check for found_pdf in this response
        for block in response.content:
            if getattr(block, "type", "") == "tool_use" and block.name == "found_pdf":
                return block.input.get("url")

        if response.stop_reason == "end_turn":
            return None

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if getattr(block, "type", "") == "tool_use":
                    if block.name == "found_pdf":
                        return block.input.get("url")
                    result_text = _run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })
            messages.append({"role": "user", "content": tool_results})

    return None
