from pydantic import BaseModel
from datetime import datetime

class CertificateBase(BaseModel):
    user_id: int
    course_id: int

class CertificateCreate(CertificateBase):
    pass

class CertificateRead(CertificateBase):
    id: int
    issued_at: datetime

    model_config = {
        "from_attributes": True
    }
