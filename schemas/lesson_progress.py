from pydantic import BaseModel
from typing import Optional

class LessonProgressBase(BaseModel):
    lesson_id: int
    user_id: int
    completed: Optional[bool] = False

class LessonProgressCreate(LessonProgressBase):
    pass

class LessonProgressRead(LessonProgressBase):
    id: int

    model_config = {
        "from_attributes": True
    }
