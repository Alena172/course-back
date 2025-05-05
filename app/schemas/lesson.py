from pydantic import BaseModel
from typing import List, Optional
from app.schemas.block import BlockRead  # импортируем BlockRead из block.py

class LessonBase(BaseModel):
    title: str
    course_id: int

class LessonCreate(LessonBase):
    pass

class LessonRead(LessonBase):
    id: int
    blocks: Optional[List[BlockRead]] = []

    model_config = {
        "from_attributes": True
    }
