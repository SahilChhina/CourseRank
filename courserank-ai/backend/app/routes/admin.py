from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.course import Course, CourseOutline
from app.models.grading import GradingComponent
from app.models.review import Review
from app.services.syllabus_parser import parse_pdf
from app.services.grading_extractor import extract_grading

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_TYPES = {"application/pdf", "application/octet-stream"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_courses = db.query(func.count(Course.id)).scalar()
    courses_with_grading = db.query(func.count(Course.id.distinct())).join(GradingComponent).scalar()
    return {
        "total_courses": total_courses,
        "courses_with_grading": courses_with_grading,
        "courses_without_grading": total_courses - courses_with_grading,
        "total_reviews": db.query(func.count(Review.id)).scalar(),
        "total_outlines": db.query(func.count(CourseOutline.id)).scalar(),
        "flagged_reviews": db.query(func.count(Review.id)).filter(Review.is_flagged == True).scalar(),
    }


@router.post("/ingest-syllabus")
async def ingest_syllabus(
    course_id: int = Form(...),
    term: str = Form(default=""),
    year: int = Form(default=0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Parse PDF
    try:
        syllabus = parse_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse PDF: {e}")

    # Extract grading components
    result = extract_grading(syllabus)

    if not result.components:
        # Save outline even if extraction failed
        outline = CourseOutline(
            course_id=course_id,
            raw_text=syllabus.full_text[:50000],
            term=term or None,
            year=year or None,
            extraction_status="no_grading_found",
        )
        db.add(outline)
        db.commit()
        return {
            "status": "no_grading_found",
            "confidence_score": 0.0,
            "components": [],
            "notes": result.notes,
            "message": "PDF parsed but no grading scheme could be extracted. Check that the syllabus contains a grading breakdown section.",
        }

    # Save outline record
    outline = CourseOutline(
        course_id=course_id,
        raw_text=syllabus.full_text[:50000],
        term=term or None,
        year=year or None,
        extraction_status="success",
    )
    db.add(outline)
    db.flush()

    # Replace existing grading components for this course
    db.query(GradingComponent).filter(GradingComponent.course_id == course_id).delete()

    saved = []
    for comp in result.components:
        gc = GradingComponent(
            course_id=course_id,
            component_name=comp.name,
            weight=comp.weight,
            confidence_score=result.confidence_score,
            source_document=file.filename,
        )
        db.add(gc)
        saved.append({"component_name": comp.name, "weight": comp.weight})

    db.commit()

    return {
        "status": "success",
        "confidence_score": result.confidence_score,
        "components": saved,
        "total_weight": sum(c.weight for c in result.components),
        "notes": result.notes,
    }


@router.post("/find-syllabus/{course_id}")
def find_syllabus_auto(
    course_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Kick off a background web search for a public syllabus PDF for this course.
    Returns immediately; use GET /admin/find-syllabus/{course_id}/status to poll.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    def _run(cid: int, code: str, name: str):
        from app.database import SessionLocal
        from app.services.syllabus_finder import find_syllabus

        result = find_syllabus(code, name)
        if not result or not result.get("components"):
            return

        local_db = SessionLocal()
        try:
            outline = CourseOutline(
                course_id=cid,
                raw_text=result["raw_text"][:50000],
                term=None,
                year=None,
                extraction_status="auto_found",
                source_url=result.get("source_url"),
            )
            local_db.add(outline)
            local_db.flush()

            local_db.query(GradingComponent).filter(
                GradingComponent.course_id == cid
            ).delete()

            for comp in result["components"]:
                local_db.add(GradingComponent(
                    course_id=cid,
                    component_name=comp["name"],
                    weight=comp["weight"],
                    confidence_score=result["confidence"],
                    source_document="auto_web_search",
                ))
            local_db.commit()
        finally:
            local_db.close()

    background_tasks.add_task(_run, course_id, course.course_code, course.course_name)
    return {"status": "searching", "message": f"Searching for {course.course_code} syllabus in background"}


@router.post("/find-syllabus-batch")
def find_syllabus_batch(
    background_tasks: BackgroundTasks,
    limit: int = 20,
    force: bool = False,
    departments: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Find syllabuses for up to `limit` courses.

    - force=true: re-process courses that already have grading.
    - departments=CS,ECE: only process courses from these dept prefixes.
    - Skips courses previously marked not_found unless force=true.
    """
    from app.models.grading import GradingComponent as GC

    dept_list = [d.strip().upper() for d in departments.split(",")] if departments else []

    if force:
        q = db.query(Course)
    else:
        # Exclude courses with no grading AND already attempted (not_found outline exists)
        already_tried = (
            db.query(CourseOutline.course_id)
            .filter(CourseOutline.extraction_status == "not_found")
            .subquery()
        )
        q = (
            db.query(Course)
            .outerjoin(GC, GC.course_id == Course.id)
            .filter(GC.id.is_(None))
            .filter(Course.id.notin_(already_tried))
        )

    if dept_list:
        from sqlalchemy import or_
        q = q.filter(or_(*[Course.course_code.like(f"{d} %") for d in dept_list]))

    courses_without = q.limit(limit).all()
    course_data = [(c.id, c.course_code, c.course_name) for c in courses_without]

    def _run_batch(course_list):
        from app.database import SessionLocal
        from app.services.syllabus_finder import find_syllabus
        import time, random

        for cid, code, name in course_list:
            try:
                result = find_syllabus(code, name)
            except Exception as e:
                print(f"find_syllabus failed for {code}: {e}")
                time.sleep(random.uniform(2, 4))
                continue

            if not result or not result.get("components"):
                # Mark as attempted so future batches skip this course
                local_db = SessionLocal()
                try:
                    local_db.add(CourseOutline(
                        course_id=cid,
                        raw_text=None,
                        term=None,
                        year=None,
                        extraction_status="not_found",
                    ))
                    local_db.commit()
                except Exception:
                    local_db.rollback()
                finally:
                    local_db.close()
                time.sleep(random.uniform(2, 4))
                continue

            # Quality gate: only replace existing grading if scraped components
            # sum to ≥85%. Otherwise the extractor likely missed real rows and
            # we'd end up showing a partial breakdown like just exams.
            total_weight = sum(c["weight"] for c in result["components"])
            if total_weight < 75:
                print(f"Skipping {code}: scraped total {total_weight}% below 75% threshold")
                time.sleep(random.uniform(2, 4))
                continue

            local_db = SessionLocal()
            try:
                outline = CourseOutline(
                    course_id=cid,
                    raw_text=result["raw_text"][:50000],
                    term=None,
                    year=None,
                    extraction_status="auto_found",
                    source_url=result.get("source_url"),
                )
                local_db.add(outline)
                local_db.flush()

                local_db.query(GradingComponent).filter(
                    GradingComponent.course_id == cid
                ).delete()

                for comp in result["components"]:
                    local_db.add(GradingComponent(
                        course_id=cid,
                        component_name=comp["name"],
                        weight=comp["weight"],
                        confidence_score=result["confidence"],
                        source_document="auto_web_search",
                    ))
                local_db.commit()
            finally:
                local_db.close()

            time.sleep(random.uniform(5, 10))

    background_tasks.add_task(_run_batch, course_data)
    return {
        "status": "batch_started",
        "courses_queued": len(course_data),
        "departments": dept_list or "all",
        "force": force,
    }


@router.post("/analyze-sentiment/{course_id}")
def analyze_sentiment(
    course_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Scrape r/uwo for mentions of this course, run VADER sentiment, and save.
    Runs in background — poll the course endpoint to see when it appears.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    def _run(cid: int, code: str):
        from app.database import SessionLocal
        from app.models.sentiment import SentimentResult
        from app.services.reddit_scraper import fetch_course_snippets
        from app.services.sentiment_analyzer import analyze, TextItem

        snippets = fetch_course_snippets(code, max_posts=15, max_snippets=80)

        # Also incorporate existing reviews from our DB
        local_db = SessionLocal()
        try:
            reviews = local_db.query(Review).filter(
                Review.course_id == cid,
                Review.is_flagged == False,
                Review.review_text.isnot(None),
            ).all()

            items = []
            for snip in snippets:
                weight = 1.0 + min(snip.score / 10.0, 3.0) if snip.score > 0 else 1.0
                items.append(TextItem(text=snip.text, weight=weight))
            for r in reviews:
                if r.review_text:
                    items.append(TextItem(text=r.review_text, weight=1.5))

            if not items:
                return

            result = analyze(items)
            if not result:
                return

            # Upsert sentiment result
            existing = local_db.query(SentimentResult).filter(
                SentimentResult.course_id == cid
            ).first()

            if existing:
                existing.overall_sentiment = result.overall_sentiment
                existing.sentiment_score = result.sentiment_score
                existing.positive_themes = result.positive_themes
                existing.negative_themes = result.negative_themes
                existing.neutral_themes = result.neutral_themes
                existing.summary = result.summary
                existing.confidence_score = result.confidence_score
            else:
                local_db.add(SentimentResult(
                    course_id=cid,
                    overall_sentiment=result.overall_sentiment,
                    sentiment_score=result.sentiment_score,
                    positive_themes=result.positive_themes,
                    negative_themes=result.negative_themes,
                    neutral_themes=result.neutral_themes,
                    summary=result.summary,
                    confidence_score=result.confidence_score,
                ))
            local_db.commit()
        finally:
            local_db.close()

    background_tasks.add_task(_run, course_id, course.course_code)
    return {
        "status": "analyzing",
        "message": f"Scraping r/uwo for {course.course_code} mentions and running sentiment analysis",
    }


@router.post("/analyze-sentiment-batch")
def analyze_sentiment_batch(
    background_tasks: BackgroundTasks,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Run sentiment analysis for up to `limit` courses without existing data."""
    from app.models.sentiment import SentimentResult

    courses_without = (
        db.query(Course)
        .outerjoin(SentimentResult, SentimentResult.course_id == Course.id)
        .filter(SentimentResult.id.is_(None))
        .limit(limit)
        .all()
    )
    course_data = [(c.id, c.course_code) for c in courses_without]

    def _run_batch(course_list):
        import time, random
        from app.database import SessionLocal
        from app.models.sentiment import SentimentResult
        from app.services.reddit_scraper import fetch_course_snippets
        from app.services.sentiment_analyzer import analyze, TextItem

        for cid, code in course_list:
            try:
                snippets = fetch_course_snippets(code, max_posts=10, max_snippets=50)
                if not snippets:
                    time.sleep(random.uniform(2, 4))
                    continue

                items = []
                for snip in snippets:
                    weight = 1.0 + min(snip.score / 10.0, 3.0) if snip.score > 0 else 1.0
                    items.append(TextItem(text=snip.text, weight=weight))

                local_db = SessionLocal()
                try:
                    reviews = local_db.query(Review).filter(
                        Review.course_id == cid,
                        Review.is_flagged == False,
                        Review.review_text.isnot(None),
                    ).all()
                    for r in reviews:
                        if r.review_text:
                            items.append(TextItem(text=r.review_text, weight=1.5))

                    result = analyze(items)
                    if not result:
                        continue

                    existing = local_db.query(SentimentResult).filter(
                        SentimentResult.course_id == cid
                    ).first()
                    if existing:
                        existing.overall_sentiment = result.overall_sentiment
                        existing.sentiment_score = result.sentiment_score
                        existing.positive_themes = result.positive_themes
                        existing.negative_themes = result.negative_themes
                        existing.neutral_themes = result.neutral_themes
                        existing.summary = result.summary
                        existing.confidence_score = result.confidence_score
                    else:
                        local_db.add(SentimentResult(
                            course_id=cid,
                            overall_sentiment=result.overall_sentiment,
                            sentiment_score=result.sentiment_score,
                            positive_themes=result.positive_themes,
                            negative_themes=result.negative_themes,
                            neutral_themes=result.neutral_themes,
                            summary=result.summary,
                            confidence_score=result.confidence_score,
                        ))
                    local_db.commit()
                finally:
                    local_db.close()
            except Exception as e:
                print(f"Error analyzing {code}: {e}")

            time.sleep(random.uniform(3, 6))

    background_tasks.add_task(_run_batch, course_data)
    return {
        "status": "batch_started",
        "courses_queued": len(course_data),
    }


@router.post("/scrape-calendar")
def scrape_calendar(
    background_tasks: BackgroundTasks,
    all_subjects: bool = False,
    subjects: Optional[str] = None,
):
    """Scrape Western Academic Calendar in the background.

    - Default: scrape PRIORITY_SUBJECTS (~29 subjects, ~3-5 min).
    - all_subjects=true: scrape ALL_SUBJECTS (~130 subjects, ~10-15 min).
    - subjects="COMPSCI,MATH,SE": scrape just these.
    """
    from app.scripts.scrape_calendar import (
        PRIORITY_SUBJECTS, ALL_SUBJECTS, run,
    )

    if subjects:
        targets = [s.strip().upper() for s in subjects.split(",") if s.strip()]
    elif all_subjects:
        targets = ALL_SUBJECTS
    else:
        targets = PRIORITY_SUBJECTS

    def _run_scrape(subject_list):
        try:
            run(subject_list)
        except Exception as e:
            print(f"Calendar scrape failed: {e}")

    background_tasks.add_task(_run_scrape, targets)
    return {
        "status": "scrape_started",
        "subjects_queued": len(targets),
        "estimated_minutes": round(len(targets) * 6 / 60, 1),
    }


@router.post("/reseed")
def reseed_database(db: Session = Depends(get_db)):
    """Clear all course data and re-seed with updated starter data."""
    from app.models.grading import GradingComponent
    from app.models.review import Review
    from app.models.sentiment import CourseScore, SentimentResult
    from app.models.course import SearchLog, CourseOutline

    db.query(SearchLog).delete()
    db.query(GradingComponent).delete()
    db.query(Review).delete()
    db.query(CourseScore).delete()
    db.query(SentimentResult).delete()
    db.query(CourseOutline).delete()
    db.query(Course).delete()
    db.commit()

    from app.seed import seed
    seed()

    total = db.query(func.count(Course.id)).scalar()
    return {"status": "success", "courses_seeded": total}


@router.post("/reprocess-course/{course_id}")
def reprocess_course(course_id: int, db: Session = Depends(get_db)):
    """Re-run grading extraction on the most recent stored syllabus text."""
    outline = (
        db.query(CourseOutline)
        .filter(CourseOutline.course_id == course_id, CourseOutline.raw_text.isnot(None))
        .order_by(CourseOutline.created_at.desc())
        .first()
    )
    if not outline or not outline.raw_text:
        raise HTTPException(status_code=404, detail="No stored syllabus text found for this course")

    from app.services.syllabus_parser import ParsedSyllabus
    syllabus = ParsedSyllabus(full_text=outline.raw_text, pages=[outline.raw_text], tables=[])
    result = extract_grading(syllabus)

    db.query(GradingComponent).filter(GradingComponent.course_id == course_id).delete()
    for comp in result.components:
        db.add(GradingComponent(
            course_id=course_id,
            component_name=comp.name,
            weight=comp.weight,
            confidence_score=result.confidence_score,
            source_document="reprocessed",
        ))

    outline.extraction_status = "reprocessed"
    db.commit()

    return {
        "status": "reprocessed",
        "confidence_score": result.confidence_score,
        "components": [{"component_name": c.name, "weight": c.weight} for c in result.components],
    }
