from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Lesson(Base):
    __tablename__ = 'lessons'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey("course.id"))

    course = relationship("Course", back_populates="lessons")
    blocks = relationship("Block", back_populates="lesson", cascade="all, delete")
    progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")

