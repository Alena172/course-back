from datetime import datetime
from sqlalchemy.orm import Session
from app.models.lesson import Lesson
from app.models.user import User
from app.models.lesson_progress import LessonProgress


def find_by_user_and_lesson(db: Session, user: User, lesson: Lesson) -> LessonProgress | None:
    return db.query(LessonProgress).filter_by(user_id=user.id, lesson_id=lesson.id).first()


def save_lesson_progress(db: Session, lesson_progress: LessonProgress):
    db.add(lesson_progress)
    db.commit()
    db.refresh(lesson_progress)
    return lesson_progress


def start_or_update_lesson_progress(db: Session, user: User, lesson: Lesson) -> LessonProgress:
    progress = find_by_user_and_lesson(db, user, lesson)
    if not progress:
        progress = LessonProgress(user=user, lesson=lesson)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def has_completed_lesson(db: Session, user: User, lesson: Lesson) -> bool:
    progress = find_by_user_and_lesson(db, user, lesson)
    return progress.is_completed if progress else False


def mark_completed(db: Session, user: User, lesson: Lesson):
    if not user or not lesson:
        return False
        
    progress = db.query(LessonProgress).filter(
        LessonProgress.user_id == user.id,
        LessonProgress.lesson_id == lesson.id
    ).first()
    
    if not progress:
        progress = LessonProgress(
            user_id=user.id,
            lesson_id=lesson.id,
            is_completed=True
        )
        db.add(progress)
    else:
        progress.is_completed = True
    
    db.commit()
    return True