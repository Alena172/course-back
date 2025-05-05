from sqlalchemy import Column, DateTime, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from enum import Enum as PyEnum
from datetime import datetime

class RoleEnum(str, PyEnum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)
    email = Column(String, unique=True)
    phone = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(Enum(RoleEnum), default=RoleEnum.STUDENT)
    
    enrollments = relationship("Enrollment", back_populates="user")
    certificates = relationship("Certificate", back_populates="user")
    progress = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")