from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class ReviewCreate(BaseModel):
    professor_name: Optional[str] = None
    term_taken: Optional[str] = None
    difficulty_rating: Optional[int] = None
    workload_rating: Optional[int] = None
    hours_per_week: Optional[float] = None
    organization_rating: Optional[int] = None
    assessment_fairness_rating: Optional[int] = None
    usefulness_rating: Optional[int] = None
    review_text: Optional[str] = None
    would_recommend: Optional[bool] = None

    @field_validator("difficulty_rating", "workload_rating", "organization_rating",
                     "assessment_fairness_rating", "usefulness_rating", mode="before")
    @classmethod
    def rating_range(cls, v):
        if v is not None and not (1 <= v <= 10):
            raise ValueError("Rating must be between 1 and 10")
        return v


class ReviewOut(BaseModel):
    id: int
    professor_name: Optional[str] = None
    term_taken: Optional[str] = None
    difficulty_rating: Optional[int] = None
    workload_rating: Optional[int] = None
    hours_per_week: Optional[float] = None
    organization_rating: Optional[int] = None
    assessment_fairness_rating: Optional[int] = None
    usefulness_rating: Optional[int] = None
    review_text: Optional[str] = None
    would_recommend: Optional[bool] = None
    created_at: datetime

    model_config = {"from_attributes": True}
