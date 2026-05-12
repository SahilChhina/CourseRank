from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(20), unique=True, nullable=False, index=True)
    course_name = Column(Text, nullable=False)
    department = Column(Text)
    description = Column(Text)
    prerequisites = Column(JSON, default=list)
    antirequisites = Column(JSON, default=list)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    outlines = relationship("CourseOutline", back_populates="course", cascade="all, delete-orphan")
    grading_components = relationship("GradingComponent", back_populates="course", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="course", cascade="all, delete-orphan")
    scores = relationship("CourseScore", back_populates="course", uselist=False, cascade="all, delete-orphan")
    sentiment = relationship("SentimentResult", back_populates="course", uselist=False, cascade="all, delete-orphan")
    search_logs = relationship("SearchLog", back_populates="matched_course")


class CourseOutline(Base):
    __tablename__ = "course_outlines"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    source_url = Column(Text)
    file_path = Column(Text)
    raw_text = Column(Text)
    term = Column(Text)
    year = Column(Integer)
    extraction_status = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    course = relationship("Course", back_populates="outlines")


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text)
    matched_course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    matched_course = relationship("Course", back_populates="search_logs")
