from pydantic import BaseModel
from enum import Enum

class EnrollmentStatus(str, Enum):
    ENROLLED = "ENROLLED"
    COMPLETED = "COMPLETED"

class EnrollmentBase(BaseModel):
    user_id: int
    course_id: int
    status: EnrollmentStatus = EnrollmentStatus.ENROLLED

class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentRead(EnrollmentBase):
    id: int

    model_config = {
        "from_attributes": True
    }

