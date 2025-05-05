from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import List, Optional
from app.models.course import Course, StatusEnum
from app.models.user import User, RoleEnum
from app.schemas.course import CourseCreate
import logging
from sqlalchemy.orm import joinedload 

logger = logging.getLogger("course_service")


# ✅ Добавить курс
def add_course(db: Session, course_data: CourseCreate):
    instructor = None
    if course_data.instructor_id:
        instructor = db.query(User).filter(User.id == course_data.instructor_id).first()
        if not instructor:
            raise ValueError("Преподаватель не найден")
        if instructor.role != RoleEnum.TEACHER:
            raise ValueError("Пользователь не является преподавателем")

    new_course = Course(
        title=course_data.title,
        description=course_data.description,
        price=course_data.price,
        category=course_data.category,
        duration=course_data.duration,
        status=course_data.status,
        image=course_data.image,
        instructor_id=course_data.instructor_id
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


# ✅ Обновить курс
def update_course(db: Session, course_id: int, updated_data: CourseCreate):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError("Курс не найден")

    # Обновляем основные поля
    course.title = updated_data.title
    course.description = updated_data.description
    course.price = updated_data.price
    course.category = updated_data.category
    course.duration = updated_data.duration
    course.status = updated_data.status
    course.image = updated_data.image

    # Обрабатываем преподавателя
    if updated_data.instructor_id:
        instructor = db.query(User).filter(
            User.id == updated_data.instructor_id,
            User.role == RoleEnum.TEACHER
        ).first()
        if not instructor:
            raise ValueError("Преподаватель не найден или не имеет соответствующей роли")
        course.instructor_id = instructor.id
    else:
        course.instructor_id = None

    db.commit()
    db.refresh(course)
    return course
# def update_course(db: Session, course_id: int, updated_data: CourseCreate):
#     course = db.query(Course).filter(Course.id == course_id).first()
#     if not course:
#         raise ValueError("Курс не найден")

#     course.title = updated_data.title
#     course.description = updated_data.description
#     course.price = updated_data.price
#     course.category = updated_data.category
#     course.duration = updated_data.duration
#     course.status = updated_data.status
#     course.image = updated_data.image

#     if updated_data.instructor_id:
#         instructor = db.query(User).filter(User.id == updated_data.instructor_id).first()
#         if not instructor:
#             raise ValueError("Преподаватель не найден")
#         if instructor.role != RoleEnum.TEACHER:
#             raise ValueError("Пользователь не является преподавателем")
#         course.instructor = instructor
#     else:
#         course.instructor = None

#     db.commit()
#     db.refresh(course)
#     return course


# ✅ Проверить, существует ли курс
def course_exists(db: Session, course_id: int) -> bool:
    exists = db.query(Course).filter(Course.id == course_id).first() is not None
    logger.info(f"Проверка существования курса с ID: {course_id}: {exists}")
    return exists


# ✅ Получить все курсы
def get_all_courses(db: Session) -> List[Course]:
    courses = db.query(Course).all()
    
    # Получаем всех преподавателей одним запросом
    instructor_ids = {c.instructor_id for c in courses if c.instructor_id}
    instructors = {i.id: i for i in db.query(User).filter(User.id.in_(instructor_ids)).all()} if instructor_ids else {}
    
    # Добавляем преподавателя к каждому курсу
    for course in courses:
        if course.instructor_id:
            course.instructor = instructors.get(course.instructor_id)
        else:
            course.instructor = None
    
    return courses


# ✅ Найти курс по ID
def find_course_by_id(db: Session, course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError("Курс не найден")
    return course


# ✅ Удалить курс
def delete_course(db: Session, course_id: int):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError("Курс не найден")
    db.delete(course)
    db.commit()


# ✅ Найти всех преподавателей
def find_teachers(db: Session) -> List[User]:
    return db.query(User).filter(User.role == RoleEnum.TEACHER).all()


# ✅ Курсы конкретного преподавателя
def find_by_instructor(db: Session, instructor_id: int) -> List[Course]:
    return db.query(Course).filter(Course.instructor_id == instructor_id).all()
