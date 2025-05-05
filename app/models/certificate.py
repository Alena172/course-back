from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    issue_date = Column(DateTime, default=datetime.now)
    certificate_code = Column(String, unique=True)

    user = relationship("User", back_populates="certificates")
    course = relationship("Course")
