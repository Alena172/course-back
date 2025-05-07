from sqlalchemy import Column, DateTime, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from enum import Enum as PyEnum
from datetime import datetime

class RoleEnum(str, PyEnum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"

    @property
    def display_name(self):
        return {
            'STUDENT': 'Student',
            'TEACHER': 'Teacher',
            'ADMIN': 'Admin',
        }.get(self.value, self.value)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    email = Column(String, unique=True)
    password = Column(String)
    phone = Column(String)
    role = Column(Enum(RoleEnum), default=RoleEnum.STUDENT)
    name = Column(String)
    surname = Column(String)
    
    enrollments = relationship("Enrollment", back_populates="user")
    certificates = relationship("Certificate", back_populates="user")
    progress = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")