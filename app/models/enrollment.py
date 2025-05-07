from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class StatusEnum(str, enum.Enum):
    ENROLLED = "ENROLLED"
    COMPLETED = "COMPLETED"

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.ENROLLED)
    course_id = Column(Integer, ForeignKey("course.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
