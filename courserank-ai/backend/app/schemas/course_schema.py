from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class GradingComponentOut(BaseModel):
    id: int
    component_name: str
    weight: float
    confidence_score: Optional[float] = None

    model_config = {"from_attributes": True}


class CourseScoreOut(BaseModel):
    difficulty_score: Optional[float] = None
    workload_score: Optional[float] = None
    organization_score: Optional[float] = None
    assessment_fairness_score: Optional[float] = None
    usefulness_score: Optional[float] = None
    confidence_score: Optional[float] = None
    explanation: Optional[str] = None

    model_config = {"from_attributes": True}


class SentimentResultOut(BaseModel):
    overall_sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    positive_themes: Optional[List[str]] = []
    negative_themes: Optional[List[str]] = []
    neutral_themes: Optional[List[str]] = []
    summary: Optional[str] = None
    confidence_score: Optional[float] = None

    model_config = {"from_attributes": True}


class CourseBase(BaseModel):
    course_code: str
    course_name: str
    department: Optional[str] = None
    description: Optional[str] = None
    prerequisites: Optional[List[str]] = []
    antirequisites: Optional[List[str]] = []


class CourseOut(CourseBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseDetailOut(CourseBase):
    id: int
    created_at: datetime
    grading_components: List[GradingComponentOut] = []
    scores: Optional[CourseScoreOut] = None
    sentiment: Optional[SentimentResultOut] = None

    model_config = {"from_attributes": True}


class CourseSearchResult(BaseModel):
    id: int
    course_code: str
    course_name: str
    department: Optional[str] = None
    difficulty_score: Optional[float] = None
    workload_score: Optional[float] = None
    tags: List[str] = []

    model_config = {"from_attributes": True}


class CompareRequest(BaseModel):
    course_id_a: int
    course_id_b: int
