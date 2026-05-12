from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.course import Course
from app.models.review import Review
from app.schemas.review_schema import ReviewCreate, ReviewOut
from app.services.scoring_engine import recompute_scores

router = APIRouter(prefix="/courses", tags=["reviews"])


@router.post("/{course_id}/reviews", response_model=ReviewOut, status_code=201)
def submit_review(course_id: int, body: ReviewCreate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    review = Review(course_id=course_id, **body.model_dump())
    db.add(review)
    db.flush()

    # Recompute scores immediately so the course page reflects the new review
    recompute_scores(course_id, db)
    db.commit()
    db.refresh(review)
    return review


@router.get("/{course_id}/reviews", response_model=List[ReviewOut])
def get_reviews(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return [r for r in course.reviews if not r.is_flagged]


@router.post("/{course_id}/reviews/{review_id}/flag", status_code=200)
def flag_review(course_id: int, review_id: int, db: Session = Depends(get_db)):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.course_id == course_id,
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.is_flagged = True
    recompute_scores(course_id, db)
    db.commit()
    return {"status": "flagged"}
