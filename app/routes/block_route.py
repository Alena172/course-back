from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.block import BlockCreate, BlockRead
from app.services import block_service
from app.auth.role_checker import RoleChecker
from app.auth.auth_bearer import JWTBearer
from fastapi import HTTPException

router = APIRouter(prefix="/blocks", tags=["Blocks"])

@router.post("/", response_model=BlockRead, dependencies=[Depends(RoleChecker(["TEACHER"]))])
def create_block(block: BlockCreate, db: Session = Depends(get_db), payload: dict = Depends(JWTBearer())):
    from services import lesson_service, course_service
    lesson = lesson_service.get_lesson_by_id(db, block.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    course = course_service.get_course_by_id(db, lesson.course_id)
    if course.instructor_id != payload["sub"]:
        raise HTTPException(status_code=403, detail="Not your course")
    return block_service.create_block(db, block)


@router.get("/by_lesson/{lesson_id}", response_model=list[BlockRead])
def get_blocks(lesson_id: int, db: Session = Depends(get_db)):
    return block_service.get_blocks_by_lesson(db, lesson_id)
