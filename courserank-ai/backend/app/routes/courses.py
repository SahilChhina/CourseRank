from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models.course import Course, SearchLog
from app.models.grading import GradingComponent
from app.models.review import Review
from app.models.sentiment import CourseScore
from app.schemas.course_schema import (
    CourseDetailOut,
    CourseSearchResult,
    CompareRequest,
    GradingComponentOut,
    CourseScoreOut,
)
from app.utils.course_code_normalizer import normalize_course_code
from app.services.tag_engine import compute_tags

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/search", response_model=list[CourseSearchResult])
def search_courses(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    normalized = normalize_course_code(query)
    pattern = f"%{query.upper()}%"
    norm_pattern = f"%{normalized}%"

    results = (
        db.query(Course)
        .filter(
            or_(
                func.upper(Course.course_code).like(pattern),
                func.upper(Course.course_code).like(norm_pattern),
                func.upper(Course.course_name).like(f"%{query.upper()}%"),
                func.upper(Course.department).like(f"%{query.upper()}%"),
            )
        )
        .limit(20)
        .all()
    )

    db.add(SearchLog(query=query, matched_course_id=results[0].id if results else None))
    db.commit()

    output = []
    for course in results:
        score = course.scores
        tags = compute_tags(course.grading_components)
        output.append(
            CourseSearchResult(
                id=course.id,
                course_code=course.course_code,
                course_name=course.course_name,
                department=course.department,
                difficulty_score=float(score.difficulty_score) if score and score.difficulty_score else None,
                workload_score=float(score.workload_score) if score and score.workload_score else None,
                tags=tags,
            )
        )
    return output


@router.get("/{course_id}", response_model=CourseDetailOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/grading", response_model=list[GradingComponentOut])
def get_grading(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course.grading_components


@router.get("/{course_id}/scores", response_model=CourseScoreOut)
def get_scores(course_id: int, db: Session = Depends(get_db)):
    score = db.query(CourseScore).filter(CourseScore.course_id == course_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="No scores available for this course")
    return score


@router.post("/compare")
def compare_courses(body: CompareRequest, db: Session = Depends(get_db)):
    course_a = db.query(Course).filter(Course.id == body.course_id_a).first()
    course_b = db.query(Course).filter(Course.id == body.course_id_b).first()

    if not course_a or not course_b:
        raise HTTPException(status_code=404, detail="One or both courses not found")

    def course_summary(course: Course):
        score = course.scores
        tags = compute_tags(course.grading_components)
        return {
            "id": course.id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "department": course.department,
            "grading_components": [
                {"component_name": g.component_name, "weight": float(g.weight)}
                for g in course.grading_components
            ],
            "scores": {
                "difficulty_score": float(score.difficulty_score) if score and score.difficulty_score else None,
                "workload_score": float(score.workload_score) if score and score.workload_score else None,
                "organization_score": float(score.organization_score) if score and score.organization_score else None,
                "usefulness_score": float(score.usefulness_score) if score and score.usefulness_score else None,
            } if score else {},
            "tags": tags,
        }

    return {"course_a": course_summary(course_a), "course_b": course_summary(course_b)}
