from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class LessonProgress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="progress")
    lesson = relationship("Lesson", back_populates="progress")
