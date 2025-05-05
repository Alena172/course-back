from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from app.models import user
from app.models.enrollment import Enrollment, StatusEnum
from app.models.user import User
from app.models.course import Course
from app.models.lesson import Lesson
from app.services.lesson_service import find_lessons_by_course
from app.services.lesson_progress_service import has_completed_lesson


# 🔍 Найти запись об участии пользователя в курсе
def find_enrollment(db: Session, user_id: int, course_id: int) -> Optional[Enrollment]:
    return db.query(Enrollment).filter_by(user_id=user_id, course_id=course_id).first()


def has_active_enrollment(db: Session, user_id: int, course_id: int) -> bool:
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id,
        Enrollment.status == StatusEnum.ACTIVE
    ).first()
    return enrollment is not None

# ➕ Записать пользователя на курс (с проверкой существующей подписки)
def enroll_user_in_course(db: Session, user_id: int, course_id: int) -> Optional[Enrollment]:
    # Проверяем, не записан ли пользователь уже на этот курс
    existing_enrollment = find_enrollment(db, user_id, course_id)
    if existing_enrollment:
        return None  # или можно вернуть существующую запись
    
    # Создаем запись о зачислении
    enrollment = Enrollment(
        user_id=user_id,
        course_id=course_id,
        status=StatusEnum.ENROLLED,
    )

    # Добавляем в сессию, сохраняем и обновляем объект
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return enrollment


# 📋 Получить список курсов пользователя
def find_enrollments_by_student(db: Session, user: User):
    # Добавьте отладочную печать
    print(f"User type: {type(user)}")
    print(f"User attributes: {dir(user)}")
    
    if not hasattr(user, 'id'):
        raise ValueError("User object is missing 'id' attribute")
    
    return db.query(Enrollment).filter(Enrollment.user_id == user.id).all()



3
# 📈 Подсчитать прогресс по урокам
def calculate_course_completion(db: Session, user: User, course: Course) -> float:
    lessons: List[Lesson] = find_lessons_by_course(db, course.id)
    completed_lessons_count = sum(
        1 for lesson in lessons if has_completed_lesson(db, user, lesson)
    )
    if not lessons:
        return 0.0
    return (completed_lessons_count / len(lessons)) * 100


