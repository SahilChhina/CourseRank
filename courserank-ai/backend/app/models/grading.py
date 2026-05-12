from sqlalchemy import Column, Integer, Text, Numeric, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class GradingComponent(Base):
    __tablename__ = "grading_components"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    component_name = Column(Text, nullable=False)
    weight = Column(Numeric, nullable=False)
    source_document = Column(Text)
    confidence_score = Column(Numeric)
    created_at = Column(TIMESTAMP, server_default=func.now())

    course = relationship("Course", back_populates="grading_components")
