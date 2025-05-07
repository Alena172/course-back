import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Form, logger
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import decode_token
from app.models.course import Course
from app.services import course_service, enrollment_service, user_service, lesson_service, block_service, lesson_progress_service
from app.models.block import Block, BlockType
from app.models.lesson import Lesson
from app.models.user import RoleEnum, User


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


router = APIRouter()
templates = Jinja2Templates(directory="templates")

async def get_current_user(request: Request, db: Session):
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    
    try:
        email = decode_token(access_token)
        if not email:
            return None
        return user_service.get_user_by_email(db, email)
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None


def get_active_courses(db: Session) -> List[Course]:
    try:
        active_courses = db.query(Course).filter(
            Course.status == "ACTIVE"
        ).all()
        
        return active_courses
        
    except Exception as e:
        print(f"Error fetching active courses: {str(e)}")
        raise


async def verify_student_access(request: Request, db: Session) -> User:
    user = await get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=302,
            headers={"Location": "/login"},
            detail="Authorization required"
        )
    if user.role != RoleEnum.STUDENT:
        raise HTTPException(
            status_code=302,
            headers={"Location": "/teacher/courses" if user.role == RoleEnum.TEACHER else "/admin/dashboard"},
            detail="Access denied"
        )
    return user

async def verify_teacher_access(request: Request, db: Session) -> User:
    user = await get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=302,
            headers={"Location": "/login"},
            detail="Authorization required"
        )
    if user.role != RoleEnum.TEACHER:
        raise HTTPException(
            status_code=403,
            detail="Teacher access required"
        )
    return user


@router.get("/courses")
async def show_courses(
    request: Request,
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, db)
    courses = get_active_courses(db)
    return templates.TemplateResponse(
        "courses_student.html",
        {
            "request": request,
            "courses": courses,
            "current_user": user
        }
    )


@router.get("/course-details/{id}", response_class=HTMLResponse)
async def get_course_details(
    id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, db)
    course = course_service.find_course_by_id(db, id)
    
    enrollment = None
    if user:
        enrollment = enrollment_service.find_enrollment(db, user.id, id)
    
    return templates.TemplateResponse("course-details.html", {
        "request": request,
        "course": course,
        "user": user,
        "enrollment": enrollment
    })

@router.get("/myaccount/courses/{course_id}/lessons", response_class=HTMLResponse)
async def view_course_lessons(
    course_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=302)
        course = course_service.find_course_by_id(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Курс не найден")
        print(user.id)
        enrollment = enrollment_service.find_enrollments_by_student(db, user)
        if not enrollment:
            return RedirectResponse("/myaccount", status_code=302)
        lessons = lesson_service.find_lessons_by_course(db, course.id)
        progress_map = {
            lesson.id: lesson_progress_service.has_completed_lesson(db, user, lesson)
            for lesson in lessons
        }
        return templates.TemplateResponse(
            "course_lessons.html",
            {
                "request": request,
                "course": course,
                "lessons": lessons,
                "lessonProgressMap": progress_map
            }
        )
        
    except Exception as e:
        print(f"Error in view_course_lessons: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/teacher/courses", response_class=HTMLResponse)
async def view_teacher_courses(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=302)
        if user.role != RoleEnum.TEACHER:
            return RedirectResponse("/courses", status_code=302)
        courses = course_service.find_by_instructor(db, user.id)
        return templates.TemplateResponse(
            "teacher_courses.html",
            {
                "request": request,
                "courses": courses
            }
        )
        
    except Exception as e:
        print(f"Error in view_teacher_courses: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/teacher/courses/{course_id}/lessons", response_class=HTMLResponse)
async def view_course_lessons(
    request: Request,
    course_id: int,
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.TEACHER:
            return RedirectResponse("/login", status_code=302)
        course = course_service.find_course_by_id(db, course_id)
        lessons = lesson_service.find_lessons_by_course(db, course_id)
        
        return templates.TemplateResponse(
            "teacher_course_lessons.html",
            {
                "request": request,
                "course": course,
                "lessons": lessons
            }
        )
        
    except Exception as e:
        logger.error(f"Error in view_course_lessons: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/teacher/courses/{course_id}/lessons/new", response_class=HTMLResponse)
async def show_create_lesson_form(
    request: Request,
    course_id: int,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Attempting to show create lesson form for course {course_id}")
        user = await get_current_user(request, db)
        if not user:
            logger.warning("Unauthorized access attempt - no user")
            return RedirectResponse("/login", status_code=302)
        
        if user.role != RoleEnum.TEACHER:
            logger.warning(f"Access denied for user {user.id} - not a teacher")
            return RedirectResponse("/courses", status_code=302)
        
        course = course_service.find_course_by_id(db, course_id)
        if not course:
            logger.error(f"Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        if course.instructor_id != user.id:
            logger.warning(f"Access denied - course {course_id} doesn't belong to teacher {user.id}")
            raise HTTPException(status_code=403, detail="Доступ запрещен: Курс не принадлежит этому учителю")
        
        lesson = {
            "id": None,
            "title": "",
            "course_id": course_id,
            "blocks": [{
                "id": None,
                "title": "",
                "type": "TEXT",
                "content": ""
            }]
        }
        
        logger.info(f"Rendering form for new lesson in course {course_id}")
        return templates.TemplateResponse(
            "teacher-create-lesson.html",
            {
                "request": request,
                "course": course,
                "lesson": lesson
            }
        )
        
    except HTTPException as he:
        logger.error(f"HTTPException in show_create_lesson_form: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in show_create_lesson_form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/teacher/courses/{course_id}/lessons/{lesson_id}/edit", response_class=HTMLResponse)
async def show_edit_lesson_form(
    request: Request,
    course_id: int,
    lesson_id: int,
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.TEACHER:
            return RedirectResponse("/login", status_code=302)
        
        course = course_service.find_course_by_id(db, course_id)
        lesson = lesson_service.find_by_id(db, lesson_id)
        
        if not course or not lesson:
            raise HTTPException(status_code=404, detail="Курс или урок не найден")
        if course.instructor_id != user.id or lesson.course_id != course_id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        return templates.TemplateResponse(
            "teacher-create-lesson.html",
            {
                "request": request,
                "course": course,
                "lesson": lesson
            }
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in show_edit_lesson_form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/teacher/courses/{course_id}/lessons/{lesson_id}/delete", response_class=HTMLResponse)
async def delete_lesson_form(
    request: Request,
    course_id: int,
    lesson_id: int,
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.TEACHER:
            return RedirectResponse("/login", status_code=302)
        
        course = course_service.find_course_by_id(db, course_id)
        lesson = lesson_service.find_by_id(db, lesson_id)
        
        if not course or not lesson:
            raise HTTPException(status_code=404, detail="Курс или урок не найден")
        if course.instructor_id != user.id or lesson.course_id != course_id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        lesson_service.delete_lesson_by_id(db, lesson_id)
        return RedirectResponse(f"/teacher/courses/{course_id}/lessons", status_code=303)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting lesson: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error deleting lesson")


@router.post("/teacher/courses/{course_id}/lessons/{lesson_id}", response_class=HTMLResponse)
async def update_lesson_form(
    request: Request,
    course_id: int,
    lesson_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    blockTitle: List[str] = Form(...),
    blockType: List[str] = Form(...),
    blockContent: List[str] = Form(...)
):
    try:
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.TEACHER:
            return RedirectResponse("/login", status_code=302)
        
        course = course_service.find_course_by_id(db, course_id)
        lesson = lesson_service.find_by_id(db, lesson_id)
        
        if not course or not lesson:
            raise HTTPException(status_code=404, detail="Курс или урок не найден")
        if course.instructor_id != user.id or lesson.course_id != course_id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        lesson_data = {
            "title": title,
            "course_id": course_id,
            "blocks": []
        }
        
        for i in range(len(blockType)):
            lesson_data["blocks"].append({
                "title": blockTitle[i] if i < len(blockTitle) else "",
                "type": blockType[i],
                "content": blockContent[i] if i < len(blockContent) else ""
            })
        
        lesson_service.save_lesson(db, lesson_data, lesson_id)
        return RedirectResponse(f"/teacher/courses/{course_id}/lessons", status_code=303)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating lesson: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error updating lesson")
    

@router.post("/teacher/courses/{course_id}/lessons", response_class=HTMLResponse)
async def create_lesson_form(
    request: Request,
    course_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    blockTitle: List[str] = Form(...),
    blockType: List[str] = Form(...),
    blockContent: List[str] = Form(...)
):
    try:
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.TEACHER:
            return RedirectResponse("/login", status_code=302)
        
        course = course_service.find_course_by_id(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Курс не найден")
        if course.instructor_id != user.id:
            raise HTTPException(status_code=403, detail="Доступ запрещен: Курс не принадлежит этому учителю")
        lesson_data = {
            "title": title,
            "course_id": course_id,
            "blocks": []
        }
        for i in range(len(blockType)):
            lesson_data["blocks"].append({
                "title": blockTitle[i] if i < len(blockTitle) else "",
                "type": blockType[i],
                "content": blockContent[i] if i < len(blockContent) else ""
            })
        lesson_service.save_lesson(db, lesson_data)
        return RedirectResponse(f"/teacher/courses/{course_id}/lessons", status_code=303)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating lesson: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error creating lesson")

@router.post("/teacher/courses/{course_id}/lessons/{lesson_id}/blocks/{block_id}/delete", response_class=HTMLResponse)
async def delete_block_form(
    request: Request,
    course_id: int,
    lesson_id: int,
    block_id: int,
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.TEACHER:
            return RedirectResponse("/login", status_code=302)
        
        course = course_service.find_course_by_id(db, course_id)
        lesson = lesson_service.find_by_id(db, lesson_id)
        
        if not course or not lesson:
            raise HTTPException(status_code=404, detail="Курс или урок не найден")
        if course.instructor_id != user.id or lesson.course_id != course_id:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        block_service.delete_block(db, block_id)
        return RedirectResponse(f"/teacher/courses/{course_id}/lessons/{lesson_id}/edit", status_code=303)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting block: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error deleting block")

@router.post("/myaccount/courses/{course_id}/lessons/{lesson_id}/complete")
async def mark_lesson_complete(
    course_id: int,
    lesson_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=302)
            
        lesson = lesson_service.find_by_id(db, lesson_id)
        if not lesson or lesson.course_id != course_id:
            raise HTTPException(status_code=404, detail="Урок не найден")
        lesson_progress_service.mark_completed(db, user, lesson)
        
        return RedirectResponse(
            f"/myaccount/courses/{course_id}/lessons",
            status_code=302
        )
        
    except Exception as e:
        print(f"Error in mark_lesson_complete: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.get("/myaccount/courses/{course_id}/lessons/{lesson_id}", response_class=HTMLResponse)
async def view_lesson(
    request: Request,
    course_id: int,
    lesson_id: int,
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=302)
        course = course_service.find_course_by_id(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Курс не найден")
        enrollment = enrollment_service.find_enrollment(db, user.id, course_id)
        if not enrollment:
            return RedirectResponse("/myaccount", status_code=302)
        lesson = lesson_service.find_by_id(db, lesson_id)
        if not lesson or lesson.course_id != course_id:
            raise HTTPException(status_code=404, detail="Урок не найден")
        is_completed = lesson_progress_service.has_completed_lesson(db, user, lesson)
        return templates.TemplateResponse(
            "lesson_details.html", 
            {
                "request": request,
                "course": course,     
                "lesson": lesson, 
                "is_completed": is_completed
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Ошибка в view_lesson: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")