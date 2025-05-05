from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.role_checker import RoleChecker
from app.services import course_service
from fastapi import HTTPException
from app.auth.auth_bearer import JWTBearer
from app.schemas.lesson import LessonCreate, LessonRead
from app.services import lesson_service

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.post("/", response_model=LessonRead, dependencies=[Depends(RoleChecker(["Teacher"]))])
def create_lesson(lesson: LessonCreate, db: Session = Depends(get_db), payload: dict = Depends(JWTBearer())):
    course = course_service.get_course_by_id(db, lesson.course_id)
    if course.instructor_id != payload["sub"]:
        raise HTTPException(status_code=403, detail="You can only add lessons to your own courses")
    return lesson_service.create_lesson(db, lesson)

@router.get("/by_course/{course_id}", response_model=list[LessonRead])
def get_lessons(course_id: int, db: Session = Depends(get_db)):
    return lesson_service.get_lessons_by_course(db, course_id)
