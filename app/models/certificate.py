from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True, index=True)
    certificate_code = Column(String, unique=True)
    issue_date = Column(DateTime, default=datetime.now)
    course_id = Column(Integer, ForeignKey("course.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="certificates")
    course = relationship("Course")
