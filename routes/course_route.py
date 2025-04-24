import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Form, logger
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from auth.auth_bearer import JWTBearer
from auth.auth_handler import decode_token
from models.course import Course
from services import course_service, enrollment_service, user_service, lesson_service, block_service, lesson_progress_service
from models.block import Block, BlockType
from models.lesson import Lesson
from models.user import RoleEnum

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем обработчик для вывода в консоль
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 🔐 Получение текущего пользователя по JWT токену
async def get_current_user(request: Request, db: Session):
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None
    
    try:
        # Декодируем токен и получаем email
        email = decode_token(access_token)
        if not email:
            return None
        return user_service.get_user_by_email(db, email)
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None


# 📌 /courses
# @router.get("/courses", response_class=HTMLResponse)
# def get_courses(request: Request, db: Session = Depends(get_db)):
#     user = get_current_user(request, db)
#     courses = course_service.get_all_courses(db)
#     return templates.TemplateResponse("courses_student.html", {
#         "request": request,
#         "user": user,
#         "courses": courses,
#         "message": "Курсы не найдены." if not courses else ""
#     })



def get_active_courses(db: Session) -> List[Course]:
    try:
        # Получаем только курсы со статусом ACTIVE
        active_courses = db.query(Course).filter(
            Course.status == "ACTIVE"
        ).all()
        
        return active_courses
        
    except Exception as e:
        # Логируем ошибку, если что-то пошло не так
        print(f"Error fetching active courses: {str(e)}")
        raise  # Можно заменить на возврат пустого списка [] в продакшене


@router.get("/courses")
async def show_courses(
    request: Request,
    db: Session = Depends(get_db)
):
    # Получаем пользователя (не обязательно)
    user = await get_current_user(request, db)
    
    # Получаем курсы
    courses = get_active_courses(db)
    
    return templates.TemplateResponse(
        "courses_student.html",
        {
            "request": request,
            "courses": courses,
            "current_user": user  # Можно использовать в шаблоне
        }
    )


# 📌 /course-details/{id}
@router.get("/course-details/{id}", response_class=HTMLResponse)
async def get_course_details(id: int, request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request, db)
    course = course_service.find_course_by_id(db, id)
    return templates.TemplateResponse("course-details.html", {
        "request": request,
        "course": course,
        "userId": user.id
    })

# 📌 /myaccount/courses/{course_id}/lessons
@router.get("/myaccount/courses/{course_id}/lessons", response_class=HTMLResponse)
async def view_course_lessons(
    course_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Получаем текущего пользователя
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=302)
        
        # Получаем курс
        course = course_service.find_course_by_id(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        # Проверяем, записан ли пользователь на курс
        print(user.id)
        enrollment = enrollment_service.find_enrollments_by_student(db, user)
        if not enrollment:
            return RedirectResponse("/myaccount", status_code=302)
        
        # Получаем уроки курса
        lessons = lesson_service.find_lessons_by_course(db, course.id)
        
        # Получаем прогресс по урокам
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

# 📌 /teacher/courses
@router.get("/teacher/courses", response_class=HTMLResponse)
async def view_teacher_courses(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Получаем текущего пользователя
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=302)
        
        # Проверяем, что пользователь - преподаватель
        if user.role != RoleEnum.TEACHER:
            return RedirectResponse("/courses", status_code=302)
        
        # Получаем курсы преподавателя
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

# 📌 /teacher/courses/{course_id}/lessons
@router.get("/teacher/courses/{course_id}/lessons", response_class=HTMLResponse)
async def view_course_lessons(
    request: Request,
    course_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Проверка аутентификации и прав доступа
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.TEACHER:
            return RedirectResponse("/login", status_code=302)
        
        # Получаем курс и уроки из базы данных
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

# 📌 /teacher/courses/{course_id}/lessons/new
@router.get("/teacher/courses/{course_id}/lessons/new", response_class=HTMLResponse)
async def show_create_lesson_form(
    request: Request,
    course_id: int,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Attempting to show create lesson form for course {course_id}")
        
        # Получаем текущего пользователя
        user = await get_current_user(request, db)
        if not user:
            logger.warning("Unauthorized access attempt - no user")
            return RedirectResponse("/login", status_code=302)
        
        if user.role != RoleEnum.TEACHER:
            logger.warning(f"Access denied for user {user.id} - not a teacher")
            return RedirectResponse("/courses", status_code=302)
        
        # Получаем курс
        course = course_service.find_course_by_id(db, course_id)
        if not course:
            logger.error(f"Course not found: {course_id}")
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        if course.instructor_id != user.id:
            logger.warning(f"Access denied - course {course_id} doesn't belong to teacher {user.id}")
            raise HTTPException(status_code=403, detail="Доступ запрещен: Курс не принадлежит этому учителю")
        
        # Создаем структуру для нового урока
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

# ✅ Показать форму редактирования урока
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

# ✅ Удалить урок
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

# ✅ Обновить урок
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
        
        # Подготавливаем данные для сохранения
        lesson_data = {
            "title": title,
            "course_id": course_id,
            "blocks": []
        }
        
        # Собираем блоки
        for i in range(len(blockType)):
            lesson_data["blocks"].append({
                "title": blockTitle[i] if i < len(blockTitle) else "",
                "type": blockType[i],
                "content": blockContent[i] if i < len(blockContent) else ""
            })
        
        # Сохраняем урок
        lesson_service.save_lesson(db, lesson_data, lesson_id)
        return RedirectResponse(f"/teacher/courses/{course_id}/lessons", status_code=303)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating lesson: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error updating lesson")
    

# ✅ Создать новый урок
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
        
        # Подготавливаем данные для сохранения
        lesson_data = {
            "title": title,
            "course_id": course_id,
            "blocks": []
        }
        
        # Собираем блоки
        for i in range(len(blockType)):
            lesson_data["blocks"].append({
                "title": blockTitle[i] if i < len(blockTitle) else "",
                "type": blockType[i],
                "content": blockContent[i] if i < len(blockContent) else ""
            })
        
        # Создаем новый урок
        lesson_service.save_lesson(db, lesson_data)
        return RedirectResponse(f"/teacher/courses/{course_id}/lessons", status_code=303)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating lesson: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error creating lesson")

# ✅ Удалить блок урока
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
        
        # Отмечаем урок как пройденный
        lesson_progress_service.mark_completed(db, user, lesson)
        
        return RedirectResponse(
            f"/myaccount/courses/{course_id}/lessons/{lesson_id}",
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
        # Получаем текущего пользователя
        user = await get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=302)
        
        # Получаем курс по его ID
        course = course_service.find_course_by_id(db, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        # Проверяем, записан ли пользователь на курс
        enrollment = enrollment_service.find_enrollment(db, user.id, course_id)
        if not enrollment:
            return RedirectResponse("/myaccount", status_code=302)
        
        # Получаем урок
        lesson = lesson_service.find_by_id(db, lesson_id)
        if not lesson or lesson.course_id != course_id:
            raise HTTPException(status_code=404, detail="Урок не найден")
        
        # Проверяем, завершён ли урок
        is_completed = lesson_progress_service.has_completed_lesson(db, user, lesson)
        
        # Рендерим шаблон с необходимыми данными
        return templates.TemplateResponse(
            "lesson_details.html",  # Убедитесь, что это правильное имя вашего шаблона
            {
                "request": request,
                "course": course,       # Передаём объект курса
                "lesson": lesson,      # Передаём объект урока
                "is_completed": is_completed  # Передаём статус завершения
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Ошибка в view_lesson: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")