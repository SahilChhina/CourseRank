from sqlalchemy import Column, Integer, Text, Numeric, Boolean, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    professor_name = Column(Text)
    term_taken = Column(Text)
    difficulty_rating = Column(Integer)
    workload_rating = Column(Integer)
    hours_per_week = Column(Numeric)
    organization_rating = Column(Integer)
    assessment_fairness_rating = Column(Integer)
    usefulness_rating = Column(Integer)
    review_text = Column(Text)
    would_recommend = Column(Boolean)
    is_flagged = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    course = relationship("Course", back_populates="reviews")
