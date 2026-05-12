from sqlalchemy import Column, Integer, Text, Numeric, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from app.database import Base


class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), unique=True, nullable=False)
    overall_sentiment = Column(Text)
    sentiment_score = Column(Numeric)
    positive_themes = Column(JSON, default=list)
    negative_themes = Column(JSON, default=list)
    neutral_themes = Column(JSON, default=list)
    summary = Column(Text)
    confidence_score = Column(Numeric)
    created_at = Column(TIMESTAMP, server_default=func.now())

    course = relationship("Course", back_populates="sentiment")


class CourseScore(Base):
    __tablename__ = "course_scores"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), unique=True, nullable=False)
    difficulty_score = Column(Numeric)
    workload_score = Column(Numeric)
    organization_score = Column(Numeric)
    assessment_fairness_score = Column(Numeric)
    usefulness_score = Column(Numeric)
    confidence_score = Column(Numeric)
    explanation = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    course = relationship("Course", back_populates="scores")
