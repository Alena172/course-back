from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from app.models.user import User, RoleEnum
from app.schemas.user import UserCreate
from app.auth.auth_handler import hash_password
from sqlalchemy.exc import NoResultFound

# ✅ Найти пользователя по email
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

# ✅ Добавить нового пользователя
def create_user(db: Session, user_data: UserCreate):
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        return  # Пользователь уже существует

    new_user = User(
        name=user_data.name,
        surname=user_data.surname,
        email=user_data.email,
        phone=user_data.phone,
        role=user_data.role or RoleEnum.Student,
        created_at=datetime.utcnow(),
        password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# ✅ Обновить существующего пользователя
def save_user(db: Session, user_id: int, updated_data: UserCreate):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("Пользователь не найден")

    user.name = updated_data.name
    user.surname = updated_data.surname
    user.email = updated_data.email
    user.phone = updated_data.phone
    user.role = updated_data.role
    db.commit()
    db.refresh(user)
    return user

# ✅ Найти всех учителей
def find_teachers(db: Session) -> List[User]:
    return db.query(User).filter(User.role == RoleEnum.TEACHER).all()

# ✅ Найти всех пользователей
def find_all_users(db: Session) -> List[User]:
    return db.query(User).all()

# ✅ Найти пользователя по ID
def find_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

# ✅ Изменить пароль пользователя
def change_password(db: Session, user_id: int, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("Пользователь не найден")

    user.password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user

# ✅ Найти пользователя по имени (email)
def find_by_name(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("Пользователь не найден")
    return user

# ✅ Удалить пользователя
def delete_user(db: Session, user_id: int):
    user = find_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

    # Если преподаватель — убрать из курсов
    if user.role == RoleEnum.TEACHER:
        from models.course import Course
        db.query(Course).filter(Course.instructor_id == user.id).update({"instructor_id": None})

    db.delete(user)
    db.commit()
