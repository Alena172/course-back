from pydantic import BaseModel
from typing import Optional
from enum import Enum

class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ENROLLED = "ENROLLED"
    COMPLETE = "COMPLETE"

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration: int
    price: float
    category: str
    status: StatusEnum
    image: Optional[str] = None
    instructor_id: Optional[int] = None

class CourseCreate(CourseBase):
    pass

class CourseRead(CourseBase):
    id: int

    model_config = {
        "from_attributes": True
    }
