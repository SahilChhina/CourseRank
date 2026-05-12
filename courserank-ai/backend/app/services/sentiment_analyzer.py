"""
Sentiment Analyzer
==================
Runs VADER sentiment analysis on a collection of text snippets (Reddit posts,
comments, student reviews) and extracts positive/negative themes via keyword
frequency.

Outputs a SentimentResult ready to be saved to the DB.
"""
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


_ANALYZER = SentimentIntensityAnalyzer()


@dataclass
class TextItem:
    text: str
    weight: float = 1.0  # weight by upvotes/recency


@dataclass
class SentimentSummary:
    overall_sentiment: str           # "positive" | "negative" | "mixed" | "neutral"
    sentiment_score: float           # -1.0 to 1.0
    positive_themes: List[str]
    negative_themes: List[str]
    neutral_themes: List[str]
    summary: str
    confidence_score: float          # 0-1, based on sample size + consistency


# ── Theme extraction ──────────────────────────────────────────────────────────

POSITIVE_THEME_KEYWORDS = {
    "easy course": ["easy", "easiest", "bird course", "easy a"],
    "good professor": ["great prof", "amazing prof", "good prof", "best prof", "great instructor"],
    "well organized": ["organized", "structured", "clear", "well-run"],
    "interesting content": ["interesting", "fun", "engaging", "fascinating", "enjoyable"],
    "helpful TAs": ["helpful tas", "great tas", "good tas", "amazing tas"],
    "useful": ["useful", "practical", "applicable", "valuable"],
    "fair grading": ["fair", "lenient", "generous", "easy grader"],
    "good for GPA": ["gpa booster", "boost gpa", "easy mark", "easy grade"],
    "lots of resources": ["resources", "lecture notes", "good slides", "good textbook"],
}

NEGATIVE_THEME_KEYWORDS = {
    "very difficult": ["hard", "difficult", "brutal", "tough", "hardest", "killer"],
    "heavy workload": ["heavy workload", "tons of work", "so much work", "overwhelming", "time-consuming"],
    "bad professor": ["bad prof", "terrible prof", "worst prof", "awful prof", "rude prof"],
    "disorganized": ["disorganized", "chaotic", "confusing", "messy", "unstructured"],
    "boring": ["boring", "dry", "dull", "tedious", "uninteresting"],
    "harsh grading": ["harsh", "strict", "tough grader", "unfair grading"],
    "exam-heavy": ["exam heavy", "tough exam", "hard exam", "killer exam", "brutal exam"],
    "fast-paced": ["fast paced", "fast-paced", "rushed", "too fast"],
    "poor TAs": ["bad tas", "terrible tas", "useless tas", "unhelpful tas"],
    "stressful": ["stressful", "stress", "anxiety", "overwhelming"],
    "lots of assignments": ["lots of assignments", "many assignments", "constant assignments"],
}

NEUTRAL_THEME_KEYWORDS = {
    "math-heavy": ["calculus", "linear algebra", "proofs", "theorem", "math heavy"],
    "coding-heavy": ["coding", "programming", "java", "python", "c++"],
    "group project": ["group project", "group work", "team project"],
    "lots of reading": ["lots of reading", "heavy reading", "readings"],
    "online format": ["online", "asynchronous", "recorded lectures"],
    "in-person": ["in person", "in-person", "lectures attendance"],
    "weekly quizzes": ["weekly quiz", "weekly quizzes", "quiz every week"],
    "midterm + final": ["midterm and final", "midterm + final", "two exams"],
}


def _detect_themes(combined_text: str, theme_dict: dict) -> List[tuple]:
    """Return [(theme, count)] sorted by count desc."""
    text_lower = combined_text.lower()
    hits = []
    for theme, keywords in theme_dict.items():
        count = sum(text_lower.count(kw) for kw in keywords)
        if count > 0:
            hits.append((theme, count))
    hits.sort(key=lambda x: x[1], reverse=True)
    return hits


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyze(items: List[TextItem]) -> Optional[SentimentSummary]:
    """
    Run VADER + theme extraction on a batch of text items.
    Returns None if there isn't enough data.
    """
    if not items:
        return None

    # Weighted compound score
    total_score = 0.0
    total_weight = 0.0
    for item in items:
        if not item.text.strip():
            continue
        scores = _ANALYZER.polarity_scores(item.text)
        w = max(item.weight, 0.1)
        total_score += scores["compound"] * w
        total_weight += w

    if total_weight == 0:
        return None

    avg_score = total_score / total_weight

    # Classify overall sentiment
    if avg_score >= 0.15:
        overall = "positive"
    elif avg_score <= -0.15:
        overall = "negative"
    elif abs(avg_score) < 0.05:
        overall = "neutral"
    else:
        overall = "mixed"

    # Theme extraction
    combined = " ".join(i.text for i in items)
    pos_themes = [t for t, _ in _detect_themes(combined, POSITIVE_THEME_KEYWORDS)[:5]]
    neg_themes = [t for t, _ in _detect_themes(combined, NEGATIVE_THEME_KEYWORDS)[:5]]
    neu_themes = [t for t, _ in _detect_themes(combined, NEUTRAL_THEME_KEYWORDS)[:5]]

    # Confidence: based on sample size, capped at 0.95
    n = len(items)
    if n <= 2:
        confidence = 0.25
    elif n <= 5:
        confidence = 0.45
    elif n <= 15:
        confidence = 0.65
    elif n <= 30:
        confidence = 0.80
    else:
        confidence = 0.90

    # Summary sentence
    summary = _build_summary(overall, pos_themes, neg_themes, n)

    return SentimentSummary(
        overall_sentiment=overall,
        sentiment_score=round(avg_score, 3),
        positive_themes=pos_themes,
        negative_themes=neg_themes,
        neutral_themes=neu_themes,
        summary=summary,
        confidence_score=round(confidence, 2),
    )


def _build_summary(overall: str, pos: List[str], neg: List[str], n: int) -> str:
    """Build a short human-readable summary."""
    if overall == "positive":
        base = f"Students generally speak positively about this course"
    elif overall == "negative":
        base = f"Students often express frustration with this course"
    elif overall == "mixed":
        base = f"Student opinions are mixed on this course"
    else:
        base = f"Student sentiment is neutral on this course"

    pieces = []
    if pos:
        pieces.append(f"praised for being {', '.join(pos[:2])}")
    if neg:
        pieces.append(f"criticized for being {', '.join(neg[:2])}")

    if pieces:
        return f"{base} — {'; '.join(pieces)}. (Based on {n} mentions.)"
    return f"{base}. (Based on {n} mentions.)"
