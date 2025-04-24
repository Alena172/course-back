from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship
from database import Base
import enum

class StatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ENROLLED = "ENROLLED"
    COMPLETE = "COMPLETE"

class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    duration = Column(Integer)
    price = Column(Numeric)
    category = Column(String, nullable=False)
    status = Column(Enum(StatusEnum), nullable=False)
    image = Column(String)
    
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete")


