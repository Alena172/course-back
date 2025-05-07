from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class BlockType(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

class Block(Base):
    __tablename__ = 'blocks'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    type = Column(Enum(BlockType))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    title = Column(String)
    lesson = relationship("Lesson", back_populates="blocks")
