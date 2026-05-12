"""
Western University Academic Calendar Scraper
=============================================
Scrapes all courses from westerncalendar.uwo.ca and upserts them
into the courses table.

Usage:
    # Scrape a handful of popular subjects (fast, good for testing)
    python3 -m app.scripts.scrape_calendar --subjects COMPSCI SE MATH STATS ECE DATASCI

    # Scrape everything (slow, ~130 subjects)
    python3 -m app.scripts.scrape_calendar --all

    # Default: scrapes the PRIORITY_SUBJECTS list defined below
    python3 -m app.scripts.scrape_calendar
"""
import argparse
import random
import re
import sys
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

# ── Abbreviation overrides ────────────────────────────────────────────────────
# URL subject code → student-facing abbreviation used as course_code prefix.
# Anything not in this map keeps the URL code as-is.
ABBREV: dict[str, str] = {
    "COMPSCI":  "CS",
    "ECONOMIC": "ECO",
    "PHILOSOP": "PHIL",
    "CALCULUS":  "CALC",
    "ANTHRO":   "ANTHRO",
    "BIOLOGY":  "BIOL",
    "BIOCHEM":  "BIOCHEM",
    "CHEM":     "CHEM",
    "EARTHSCI": "EARTHSCI",
    "ENGLISH":  "ENGLISH",
    "FRENCH":   "FRENCH",
    "GEOGENV":  "GEOG",
    "HISTORY":  "HISTORY",
    "KINESIOL": "KINESIOL",
    "LINGUIST": "LINGUIST",
    "MOS":      "MOS",
    "MATH":     "MATH",
    "MUSIC":    "MUSIC",
    "NURSING":  "NURSING",
    "PHYSICS":  "PHYSICS",
    "PHYSIOL":  "PHYSIOL",
    "POLISCI":  "POLISCI",
    "PSYCHOL":  "PSYCHOL",
    "SE":       "SE",
    "SOCIOLOG": "SOC",
    "SPANISH":  "SPANISH",
    "STATS":    "STATS",
    "WRITING":  "WRITING",
    "ECE":      "ECE",
    "DATASCI":  "DATASCI",
    "NEURO":    "NEURO",
    "ACTURSCI": "ACTURSCI",
    "APPLMATH": "APPLMATH",
    "BUSINESS": "BUS",
    "MME":      "MME",
    "CEE":      "CEE",
    "BME":      "BME",
    "DIGIHUM":  "DIGIHUM",
    "FILM":     "FILM",
    "INTREL":   "INTREL",
    "MEDBIO":   "MEDBIO",
}

# Subjects to scrape by default (most-searched by Western students)
PRIORITY_SUBJECTS = [
    "COMPSCI", "SE", "ECE", "DATASCI",
    "MATH", "APPLMATH", "STATS", "CALCULUS",
    "PHYSICS", "CHEM", "BIOLOGY", "BIOCHEM",
    "PSYCHOL", "SOCIOLOG", "POLISCI", "ECONOMIC",
    "MOS", "BUSINESS",
    "KINESIOL", "NEURO", "PHYSIOL",
    "ENGLISH", "HISTORY", "PHILOSOP",
    "ACTURSCI", "BIOSTATS",
    "MME", "CEE", "BME",
]

ALL_SUBJECTS = [
    "ACTURSCI","ASL","AMERICAN","ADS","ANATCELL","AESL","ANTHRO","APPLMATH",
    "ARABIC","AH","AISE","ARTHUM","ASTRONOM","BIOCHEM","BIOLOGY","BME",
    "BIOSTATS","BLST","BUSINESS","CALCULUS","CANADIAN","CGS","CBE","CHEM",
    "CYS","CHINESE","CEE","CLASSICS","COMMSCI","COMPLIT","COMPSCI","CA",
    "DANCE","DATASCI","DIGICOMM","DIGIHUM","DISABST","EARTHSCI","EASTASIA",
    "ECONOMIC","EDUC","ECE","ELI","ENGSCI","ENGLISH","ENVIRSCI","EPID",
    "EPIDEMIO","FIMS","FAMLYSTU","FILM","FINMOD","FOODNUTR","FRENCH","GSWS",
    "GEOGENV","GERMAN","GGB","GLE","GREEK","HEALTSCI","HEBREW","HINDI",
    "HISTORY","HISTSCI","HUMANECO","HUMANRS","HUMANIT","INDIGSTU","IE",
    "INTEGSCI","ICC","INTERDIS","INTREL","ISLAMSTU","ITALIAN","ITALST",
    "JAPANESE","JEWISH","KINESIOL","KOREAN","LATIN","LAW","LS","LINGUIST",
    "MOS","MATH","MME","MSE","MEDIACOM","MBI","MEDBIO","MEDSCIEN","MEDIEVAL",
    "MICROIMM","MCS","MUSIC","NEURO","NMM","NURSING","ONEHEALT","PATHOL",
    "PERSIAN","PHARM","PHILOSOP","PHYSICS","PHYSIOL","PHYSPHRM","POLISCI",
    "PPE","PORTUGSE","PSYCHOL","PUBHEALT","REHABSCI","RELSTUD","RUSSIAN",
    "SCHOLARS","SASAH","SCIENCE","SOCLJUST","SOCSCI","SOCWORK","SOCIOLOG",
    "SE","SPANISH","SPEECH","STATS","SA","THANAT","TNLA","THEATRE","THEOLST",
    "TJ","WORLDLIT","WRITING",
]

BASE_URL = "https://www.westerncalendar.uwo.ca/Courses.cfm"
COURSE_URL = BASE_URL + "?Subject={subject}&SelectedCalendar=Live&ArchiveID="
REQUEST_DELAY_MIN = 4.0   # min seconds between requests
REQUEST_DELAY_MAX = 8.0   # max seconds between requests

# Regex: "Computer Science 1027A/B COURSE TITLE"
TITLE_RE = re.compile(r"^(.+?)\s+(\d{4}[A-Z/]*)\s+(.+)$")
# Strip trailing letter suffix from course number: "1027A/B" → "1027"
NUM_STRIP_RE = re.compile(r"[A-Z/]+$")


# ── Parsing ───────────────────────────────────────────────────────────────────

def _abbrev(subject_code: str) -> str:
    return ABBREV.get(subject_code, subject_code)


def _parse_course_code(subject_code: str, raw_number: str) -> str:
    number = NUM_STRIP_RE.sub("", raw_number)
    return f"{_abbrev(subject_code)} {number}"


def _clean_title(raw: str) -> str:
    """Title-case a course name from ALL CAPS, preserving roman numerals."""
    titled = raw.strip().title()
    # Fix roman numerals lowercased by title(): Ii→II, Iii→III, Iv→IV, Vi→VI etc.
    titled = re.sub(r"\b(I{1,3}|Iv|Vi{0,3}|Ix|Xi{0,3}|Xiv|Xix|Xx)\b",
                    lambda m: m.group(0).upper(), titled)
    return titled


def _extract_tagged_text(p_tag) -> tuple[Optional[str], str]:
    """
    Returns (label, content) for a <p><strong>Label:</strong> content</p>.
    Returns (None, full_text) if no strong tag found.
    """
    strong = p_tag.find("strong")
    if not strong:
        return None, p_tag.get_text(separator=" ", strip=True)
    label = strong.get_text(strip=True).rstrip(":").lower()
    # Content = everything in p except the strong tag
    full = p_tag.get_text(separator=" ", strip=True)
    label_text = strong.get_text(strip=True)
    content = full[len(label_text):].strip().lstrip(":").strip()
    return label, content


def _split_list(text: str) -> list[str]:
    """Split a comma/semicolon-separated prerequisite list into clean items."""
    items = re.split(r"[,;]", text)
    cleaned = []
    for item in items:
        item = item.strip().rstrip(".")
        if item and len(item) > 1:
            cleaned.append(item)
    return cleaned


def parse_subject_page(html: str, subject_code: str) -> list[dict]:
    """
    Real page structure (Bootstrap accordion):
      div.panel.panel-default
        div.panel-heading
          a > h4.courseTitleNoBlueLink   ← title
        div.panel-collapse
          div.panel-body
            div.col-xs-12 > div          ← description (no <strong>)
            div.col-xs-12 > div          ← Prerequisite(s): ...
            div.col-xs-12 > div          ← Antirequisite(s): ...
            div.col-xs-12 > div          ← Extra Information: ...
            div.col-xs-12 > h5           ← Course Weight: 0.50
    """
    soup = BeautifulSoup(html, "html.parser")
    courses = []

    for panel in soup.find_all("div", class_="panel-default"):
        # ── Title ──────────────────────────────────────────────────────────
        h4 = panel.find("h4", class_="courseTitleNoBlueLink")
        if not h4:
            continue

        # Strip the hidden-print anchor text from title
        for a in h4.find_all("a", class_="hidden-print"):
            a.decompose()
        title_text = h4.get_text(separator=" ", strip=True)

        m = TITLE_RE.match(title_text)
        if not m:
            continue

        raw_number    = m.group(2)   # "1027A/B"
        raw_name      = m.group(3)   # "COMPUTER SCIENCE FUNDAMENTALS II"
        course_code   = _parse_course_code(subject_code, raw_number)
        course_name   = _clean_title(raw_name)

        # ── Body ───────────────────────────────────────────────────────────
        body = panel.find("div", class_="panel-body")
        if not body:
            # Course may not have details available yet
            courses.append({
                "course_code":    course_code,
                "course_name":    course_name,
                "department":     _dept_name(subject_code),
                "description":    "",
                "prerequisites":  [],
                "antirequisites": [],
            })
            continue

        description   = ""
        prerequisites: list[str] = []
        antirequisites: list[str] = []

        # Each detail block is in a div.col-xs-12 > div (or h5 for weight)
        for col in body.find_all("div", class_="col-xs-12"):
            inner = col.find(["div", "h5"])
            if not inner:
                continue
            strong = inner.find("strong")
            if strong:
                label   = strong.get_text(strip=True).rstrip(":").lower()
                # Content = full text minus the strong label text
                full    = inner.get_text(separator=" ", strip=True)
                content = full[len(strong.get_text(strip=True)):].strip().lstrip(":").strip()

                if "prerequisite" in label and "anti" not in label:
                    prerequisites = _split_list(content)
                elif "antirequisite" in label:
                    antirequisites = _split_list(content)
                # skip extra info / course weight — not needed in DB
            else:
                # First untagged div = description
                if not description:
                    description = inner.get_text(separator=" ", strip=True)

        courses.append({
            "course_code":    course_code,
            "course_name":    course_name,
            "department":     _dept_name(subject_code),
            "description":    description,
            "prerequisites":  prerequisites,
            "antirequisites": antirequisites,
        })

    return courses


def _dept_name(subject_code: str) -> str:
    _DEPT = {
        "COMPSCI": "Computer Science", "SE": "Software Engineering",
        "ECE": "Electrical and Computer Engineering",
        "MATH": "Mathematics", "APPLMATH": "Applied Mathematics",
        "STATS": "Statistical and Actuarial Sciences",
        "CALCULUS": "Mathematics", "PHYSICS": "Physics",
        "CHEM": "Chemistry", "BIOLOGY": "Biology",
        "BIOCHEM": "Biochemistry", "ECONOMIC": "Economics",
        "MOS": "Management and Organizational Studies",
        "PSYCHOL": "Psychology", "POLISCI": "Political Science",
        "SOCIOLOG": "Sociology", "KINESIOL": "Kinesiology",
        "NEURO": "Neuroscience", "PHYSIOL": "Physiology",
        "ENGLISH": "English", "HISTORY": "History",
        "FILOSOP": "Philosophy", "DATASCI": "Data Science",
        "ACTURSCI": "Actuarial Science", "BIOSTATS": "Biostatistics",
        "MME": "Mechanical and Materials Engineering",
        "CEE": "Civil and Environmental Engineering",
        "BME": "Biomedical Engineering", "BUSINESS": "Business Administration",
        "DIGIHUM": "Digital Humanities", "FILM": "Film Studies",
        "INTREL": "International Relations", "MEDBIO": "Medical Biophysics",
    }
    return _DEPT.get(subject_code, subject_code.title())


# ── Database upsert ───────────────────────────────────────────────────────────

def upsert_courses(courses: list[dict], db: Session, subject_code: str) -> tuple[int, int]:
    from app.models.course import Course

    inserted = 0
    updated = 0
    seen_in_batch: set = set()

    for data in courses:
        code = data["course_code"]
        if code in seen_in_batch:
            continue
        seen_in_batch.add(code)

        existing = db.query(Course).filter(
            Course.course_code == code
        ).first()

        if existing:
            existing.course_name = data["course_name"]
            existing.department = data["department"]
            existing.description = data["description"] or existing.description
            existing.prerequisites = data["prerequisites"]
            existing.antirequisites = data["antirequisites"]
            updated += 1
        else:
            course = Course(
                course_code=code,
                course_name=data["course_name"],
                department=data["department"],
                description=data["description"],
                prerequisites=data["prerequisites"],
                antirequisites=data["antirequisites"],
            )
            db.add(course)
            inserted += 1

    db.commit()
    return inserted, updated


# ── HTTP fetch ────────────────────────────────────────────────────────────────

def fetch_subject(session: requests.Session, subject_code: str) -> Optional[str]:
    url = COURSE_URL.format(subject=subject_code)
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
            text = resp.text
            if "CAPTCHA" in text or "confirm you are" in text.lower():
                wait = 30 + attempt * 30
                print(f"\n  [CAPTCHA] Blocked on {subject_code}. Waiting {wait}s...", flush=True)
                time.sleep(wait)
                continue
            return text
        except requests.RequestException as e:
            print(f"  [WARN] Failed to fetch {subject_code} (attempt {attempt+1}): {e}")
            time.sleep(5)
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def run(subjects: list[str], dry_run: bool = False) -> None:
    from app.database import SessionLocal, engine, Base
    from app.models.course import Course  # noqa: ensure table exists

    Base.metadata.create_all(bind=engine)

    http = requests.Session()
    http.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })

    db: Session = SessionLocal()
    total_inserted = 0
    total_updated = 0
    total_courses_parsed = 0

    print(f"\n{'='*55}")
    print(f"  Western Calendar Scraper — {len(subjects)} subject(s)")
    print(f"{'='*55}\n")

    for i, subject in enumerate(subjects, 1):
        print(f"[{i:>3}/{len(subjects)}] {subject}...", end=" ", flush=True)

        html = fetch_subject(http, subject)
        if not html:
            print("SKIP")
            time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
            continue

        courses = parse_subject_page(html, subject)
        total_courses_parsed += len(courses)

        if dry_run:
            print(f"{len(courses)} courses (dry run)")
        else:
            ins, upd = upsert_courses(courses, db, subject)
            total_inserted += ins
            total_updated += upd
            print(f"{len(courses)} parsed → {ins} new, {upd} updated")

        if i < len(subjects):
            delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            time.sleep(delay)

    db.close()

    print(f"\n{'='*55}")
    print(f"  Done.")
    print(f"  Subjects scraped : {len(subjects)}")
    print(f"  Courses parsed   : {total_courses_parsed}")
    if not dry_run:
        print(f"  Inserted         : {total_inserted}")
        print(f"  Updated          : {total_updated}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Western Academic Calendar")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Scrape all subjects (~130)")
    group.add_argument("--subjects", nargs="+", metavar="SUBJECT",
                       help="Specific subject codes to scrape, e.g. COMPSCI MATH SE")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse only — do not write to database")
    args = parser.parse_args()

    if args.all:
        targets = ALL_SUBJECTS
    elif args.subjects:
        targets = [s.upper() for s in args.subjects]
    else:
        targets = PRIORITY_SUBJECTS

    run(targets, dry_run=args.dry_run)
