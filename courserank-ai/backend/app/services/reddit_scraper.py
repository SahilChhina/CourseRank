"""
Reddit Scraper for r/uwo
========================
Fetches posts and comments mentioning a specific course code using Reddit's
public JSON endpoint (no API key required).

Returns clean text snippets ready for sentiment analysis.
"""
import re
import time
import random
from dataclasses import dataclass
from typing import List, Optional

import requests

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "CourseRankAI/1.0 (educational portfolio project)"
})

REDDIT_BASE = "https://www.reddit.com"
SUBREDDIT = "uwo"
REQUEST_DELAY = 1.5  # be polite — Reddit rate-limits


@dataclass
class RedditSnippet:
    text: str
    score: int          # upvotes
    source: str         # "post" or "comment"
    permalink: str
    post_title: Optional[str] = None


def _course_patterns(course_code: str) -> List[re.Pattern]:
    """
    Build regex patterns that match a course code in various formats.
    "CS 1027" → matches "CS 1027", "CS1027", "cs1027", "Cs 1027", etc.
    """
    parts = course_code.split()
    if len(parts) != 2:
        return [re.compile(re.escape(course_code), re.IGNORECASE)]
    prefix, num = parts
    patterns = [
        re.compile(rf"\b{re.escape(prefix)}\s*{re.escape(num)}\b", re.IGNORECASE),
        re.compile(rf"\b{re.escape(prefix)}{re.escape(num)}\b", re.IGNORECASE),
    ]
    return patterns


def _mentions_course(text: str, patterns: List[re.Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


def _clean_text(text: str) -> str:
    """Strip Reddit markdown, links, and excess whitespace."""
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # [text](url) → text
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _search_posts(course_code: str, limit: int = 25) -> List[dict]:
    """Search r/uwo for posts mentioning the course code."""
    # Try both spaced and unspaced versions
    queries = [course_code, course_code.replace(" ", "")]
    all_posts = {}

    for query in queries:
        url = f"{REDDIT_BASE}/r/{SUBREDDIT}/search.json"
        params = {
            "q": query,
            "restrict_sr": "on",
            "sort": "relevance",
            "t": "year",
            "limit": limit,
        }
        try:
            resp = _SESSION.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                pid = post.get("id")
                if pid and pid not in all_posts:
                    all_posts[pid] = post
        except (requests.RequestException, ValueError):
            continue
        time.sleep(REQUEST_DELAY)

    return list(all_posts.values())


def _fetch_comments(permalink: str, limit: int = 50) -> List[dict]:
    """Fetch all comments on a post (top-level only for simplicity)."""
    url = f"{REDDIT_BASE}{permalink}.json"
    try:
        resp = _SESSION.get(url, params={"limit": limit}, timeout=15)
        if resp.status_code != 200:
            return []
        thread = resp.json()
        if len(thread) < 2:
            return []
        comments_data = thread[1].get("data", {}).get("children", [])
        results = []
        for c in comments_data:
            if c.get("kind") == "t1":
                d = c.get("data", {})
                results.append(d)
                # Walk one level of replies
                replies = d.get("replies")
                if isinstance(replies, dict):
                    for r in replies.get("data", {}).get("children", []):
                        if r.get("kind") == "t1":
                            results.append(r.get("data", {}))
        return results
    except (requests.RequestException, ValueError):
        return []


def fetch_course_snippets(
    course_code: str,
    max_posts: int = 15,
    max_snippets: int = 80,
) -> List[RedditSnippet]:
    """
    Scrape r/uwo for posts + comments mentioning the course code.
    Returns a deduplicated list of text snippets that explicitly mention the course.
    """
    patterns = _course_patterns(course_code)
    snippets: List[RedditSnippet] = []
    seen_texts: set = set()

    posts = _search_posts(course_code)[:max_posts]

    for post in posts:
        title = post.get("title", "")
        body = post.get("selftext", "")
        permalink = post.get("permalink", "")
        score = post.get("score", 0)

        post_text = f"{title}\n{body}".strip()
        if _mentions_course(post_text, patterns):
            cleaned = _clean_text(post_text)
            if cleaned and cleaned not in seen_texts and len(cleaned) > 15:
                seen_texts.add(cleaned)
                snippets.append(RedditSnippet(
                    text=cleaned,
                    score=score,
                    source="post",
                    permalink=permalink,
                    post_title=title,
                ))

        # Fetch comments if post mentions the course OR title strongly suggests relevance
        if _mentions_course(post_text, patterns) or _mentions_course(title, patterns):
            time.sleep(REQUEST_DELAY)
            comments = _fetch_comments(permalink)
            for c in comments:
                body = c.get("body", "")
                if not body or body in {"[deleted]", "[removed]"}:
                    continue
                # Comments inherit course context from parent post — accept all
                cleaned = _clean_text(body)
                if cleaned and cleaned not in seen_texts and len(cleaned) > 15:
                    seen_texts.add(cleaned)
                    snippets.append(RedditSnippet(
                        text=cleaned,
                        score=c.get("score", 0),
                        source="comment",
                        permalink=permalink,
                        post_title=title,
                    ))
                if len(snippets) >= max_snippets:
                    return snippets

        if len(snippets) >= max_snippets:
            break

    return snippets
