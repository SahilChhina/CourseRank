"""
Agentic syllabus finder.

Uses Claude (Haiku 4.5) with Anthropic's hosted server-side web_search +
web_fetch tools to find a syllabus PDF when hardcoded URL patterns and
direct DDG scraping both fail.

Critically, web_search and web_fetch run on Anthropic's infrastructure, NOT
the host running this script. That means:
  - no IP-based rate limiting
  - better search quality than DDG HTML scraping
  - works equally well from Railway, localhost, or any other host

The only client-side tool is `found_pdf` — terminal, ends the loop.
"""
import os
from typing import Optional

MAX_TURNS = 12
MODEL = "claude-haiku-4-5"

# Anthropic-hosted server-side tools. Type names are version-stable.
# - web_search_20260209 returns up to 5 results per call, scoped to uwo.ca.
# - web_fetch_20260209 fetches a URL and returns parsed content.
# - found_pdf is our terminal client-side tool.
_TOOLS = [
    {
        "type": "web_search_20260209",
        "name": "web_search",
        "max_uses": 6,
        "allowed_domains": ["uwo.ca", "westerncalendar.uwo.ca"],
    },
    {
        "type": "web_fetch_20260209",
        "name": "web_fetch",
        "max_uses": 8,
        "allowed_domains": ["uwo.ca", "westerncalendar.uwo.ca"],
    },
    {
        "name": "found_pdf",
        "description": (
            "Call this when you have identified a direct URL to the course "
            "syllabus / outline PDF. This ends the search immediately. The "
            "URL must end with .pdf and be on a uwo.ca domain."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Direct URL to the syllabus PDF.",
                },
                "reasoning": {
                    "type": "string",
                    "description": "One sentence on why this is the right PDF.",
                },
            },
            "required": ["url", "reasoning"],
        },
    },
]

_SYSTEM = """You are a research agent that finds syllabus PDFs (course outlines) for Western University courses.

GOAL: Return a direct URL to a .pdf course outline. Call the `found_pdf` tool with it.

KNOWN STRUCTURE — Western University posts outlines at these locations (search these directly when possible):
  - Computer Science:    www.csd.uwo.ca/misc/outlines/{year}-{Fall|Winter}/
  - Software Engineering: www.eng.uwo.ca/se/courses/outlines/{year}-{Fall|Winter}/
  - Math/AppliedMath:    www.math.uwo.ca/undergraduate/current_students/course_information/course-outlines-directory/{year}/
  - Statistics:          www.uwo.ca/stats/undergraduate/course-outlines/{academicyear}/
  - Physics:             physics.uwo.ca/pdfs/undergraduate/outlines_{yy}_{yy}/
  - ECE:                 www.eng.uwo.ca/electrical/undergraduate/
  - Academic Calendar:   westerncalendar.uwo.ca (has course descriptions, sometimes links to outlines)

STRATEGY:
  1. If the course's department has a known outline directory above, try web_fetch on that directory page first — it usually lists every course's PDF.
  2. Otherwise web_search for the course code with `site:uwo.ca filetype:pdf` (e.g. `"PSYCHOL 2010" outline filetype:pdf site:uwo.ca`).
  3. If results return department index pages instead of direct PDFs, web_fetch the index page and look for the course code in the link list.
  4. Prefer 2024, 2025, or 2026 outlines. Older is OK if nothing recent exists.
  5. Once you see a .pdf link that clearly matches the course (course code in the filename or surrounding text), call `found_pdf`.

RULES:
  - The URL you pass to found_pdf must end in .pdf and must be hosted on uwo.ca.
  - Never invent URLs. Only return URLs you have seen in search results or fetched pages.
  - If after 4 searches/fetches you cannot find the PDF, stop and respond with plain text saying you could not find it. Do not call found_pdf with a guess.
"""


def find_syllabus_agent(course_code: str, course_name: str) -> Optional[str]:
    """
    Drive Claude through web_search + web_fetch to locate a syllabus PDF.
    Returns the URL or None.
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
                f"Find the course outline / syllabus PDF for: "
                f"{course_code} — {course_name}\n\n"
                f"This is a Western University (London, Ontario, Canada) course. "
                f"Search the Western academic websites and return a direct .pdf URL."
            ),
        }
    ]

    for turn in range(MAX_TURNS):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=[
                    {
                        "type": "text",
                        "text": _SYSTEM,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=_TOOLS,
                messages=messages,
            )
        except Exception as e:
            print(f"[syllabus_agent] API error for {course_code} (turn {turn}): {e}")
            return None

        # Pre-scan response for our terminal client-side tool.
        for block in response.content:
            if getattr(block, "type", "") == "tool_use" and block.name == "found_pdf":
                url = block.input.get("url", "")
                if url and url.lower().endswith(".pdf"):
                    print(f"[syllabus_agent] {course_code} → {url}")
                    return url
                return None

        # Server tools (web_search / web_fetch) execute on Anthropic's side and
        # their results stream back in the same response. We just append and
        # let Claude continue reasoning.
        if response.stop_reason == "end_turn":
            return None  # Claude gave up without calling found_pdf

        if response.stop_reason == "pause_turn":
            # Server-side tool loop hit iteration limit — resume by re-sending
            messages.append({"role": "assistant", "content": response.content})
            continue

        if response.stop_reason == "tool_use":
            # Only client-side tools need explicit results. found_pdf was
            # caught above, so any remaining tool_use blocks here are server
            # tools whose results are already in the response. Just continue.
            messages.append({"role": "assistant", "content": response.content})
            # If there are no client-side tool calls to respond to, the next
            # call needs no user message — Claude will continue from its own
            # turn. But the API requires a user turn to continue, so prompt
            # it to act on what it found:
            messages.append({
                "role": "user",
                "content": "Continue. Either call found_pdf with the PDF URL, or do another search.",
            })
            continue

        return None  # unexpected stop reason

    print(f"[syllabus_agent] {course_code} hit MAX_TURNS")
    return None
