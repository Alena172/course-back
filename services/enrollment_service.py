from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from models import user
from models.enrollment import Enrollment, StatusEnum
from models.user import User
from models.course import Course
from models.lesson import Lesson
from services.lesson_service import find_lessons_by_course
from services.lesson_progress_service import has_completed_lesson


# 🔍 Найти запись об участии пользователя в курсе
def find_enrollment(db: Session, user_id: int, course_id: int) -> Optional[Enrollment]:
    return db.query(Enrollment).filter_by(user_id=user_id, course_id=course_id).first()


# ➕ Записать пользователя на курс
def enroll_user_in_course(db: Session, user_id: int, course_id: int) -> Enrollment:
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


