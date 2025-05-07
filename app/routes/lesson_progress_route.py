from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.lesson_progress import LessonProgressCreate, LessonProgressRead
from app.services import lesson_progress_service
from app.auth.auth_bearer import JWTBearer
from app.auth.role_checker import RoleChecker

router = APIRouter(
    prefix="/progress",
    tags=["Progress"],
    dependencies=[Depends(JWTBearer()), Depends(RoleChecker(["Student"]))],
)

@router.post("/", response_model=LessonProgressRead)
def add_progress(progress: LessonProgressCreate, db: Session = Depends(get_db)):
    return lesson_progress_service.create_progress(db, progress)

@router.post("/complete", response_model=LessonProgressRead, dependencies=[Depends(RoleChecker(["Student"]))])
def complete_lesson(
    user_id: int,
    lesson_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(JWTBearer())
):
    if payload["sub"] != user_id:
        raise HTTPException(status_code=403, detail="You can only mark your own progress")
    from services.lesson_service import get_lesson_by_id
    lesson = get_lesson_by_id(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    from services.enrollment_service import get_enrollments_by_user
    user_enrollments = get_enrollments_by_user(db, user_id)
    course_ids = [e.course_id for e in user_enrollments]

    if lesson.course_id not in course_ids:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")

    from services.lesson_progress_service import mark_lesson_completed
    progress = mark_lesson_completed(db, user_id, lesson_id)

    from services.lesson_service import get_lessons_by_course
    lessons = get_lessons_by_course(db, lesson.course_id)
    lesson_ids = {l.id for l in lessons}

    from services.lesson_progress_service import get_progress
    completed = {
        p.lesson_id for p in get_progress(db, user_id) if p.is_completed
    }

    if lesson_ids == completed:
        from services.certificate_service import create_certificate
        from schemas.certificate import CertificateCreate
        create_certificate(db, CertificateCreate(user_id=user_id, course_id=lesson.course_id))

    return progress


@router.get("/user/{user_id}", response_model=list[LessonProgressRead])
def get_user_progress(user_id: int, db: Session = Depends(get_db)):
    return lesson_progress_service.get_progress(db, user_id)
