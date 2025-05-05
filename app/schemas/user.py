from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional

class RoleEnum(str, Enum):
    Student = "STUDENT"
    Teacher = "TEACHER"
    Admin = "ADMIN"

class UserBase(BaseModel):
    name: str
    surname: str
    email: EmailStr
    phone: str
    role: RoleEnum

class UserLogin(BaseModel):
    email: EmailStr
    password: str

from app.models.user import RoleEnum

class UserCreate(BaseModel):
    name: str
    surname: str
    email: str
    phone: str
    password: str
    role: RoleEnum = RoleEnum.STUDENT  # Устанавливаем значение по умолчанию # Делаем поле необязательным со значением по умолчанию
class UserRead(UserBase):
    id: int

    model_config = {
    "from_attributes": True
}
