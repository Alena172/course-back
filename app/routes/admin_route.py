from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import RoleEnum, User
from app.routes.course_route import get_current_user
from app.services.course_service import find_course_by_id, add_course, delete_course, course_exists, get_all_courses, update_course
from app.services.user_service import create_user, find_all_users, find_user_by_id, save_user, delete_user, find_teachers
from app.schemas.course import CourseCreate
from app.schemas.user import UserCreate, UserRead
import logging

router = APIRouter(tags=["Admin"])
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger("admin")


async def verify_admin_access(request: Request, db: Session):
    user = await get_current_user(request, db)
    if not user or user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return user


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.ADMIN:
            return RedirectResponse("/login", status_code=302)
        
        return templates.TemplateResponse(
            "admin_dashboard.html",
            {"request": request}
        )
        
    except Exception as e:
        logger.error(f"Error in admin_dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/admin/create-or-edit-user", response_class=HTMLResponse)
async def show_user_form(
    request: Request,
    id: int = None,
    db: Session = Depends(get_db)
):
    try:
        current_user = await get_current_user(request, db)
        if not current_user or current_user.role != RoleEnum.ADMIN:
            return RedirectResponse("/login", status_code=302)
        
        user = find_user_by_id(db, id) if id else UserCreate(
            name="", surname="", email="", phone="", password="", role="STUDENT"
        )
        
        return templates.TemplateResponse(
            "admin_user_form.html",
            {
                "request": request,
                "user": user
            }
        )
    except Exception as e:
        print(f"Error in show_user_form: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/admin/create-or-edit-user", response_class=HTMLResponse)
async def process_user_form(
    request: Request,
    db: Session = Depends(get_db),
    id: str = Form(None),  # Change to str first
    name: str = Form(...),
    surname: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    try:
        # Convert id to int if it exists and is not empty
        user_id = int(id) if id and id.strip() else None
        
        user_data = UserCreate(
            name=name,
            surname=surname,
            email=email,
            phone=phone,
            password=password,
            role=role
        )
        
        if user_id:
            save_user(db, user_id, user_data)
        else:
            create_user(db, user_data)
            
        return RedirectResponse("/admin/users", status_code=303)
        
    except Exception as e:
        print(f"Error in process_user_form: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ✅ Список пользователей
@router.get("/admin/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Проверка прав администратора
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.ADMIN:
            return RedirectResponse("/login", status_code=302)
        
        users = find_all_users(db)
        return templates.TemplateResponse(
            "admin_user_list.html",
            {
                "request": request,
                "users": users
            }
        )
    except Exception as e:
        print(f"Error in list_users: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/admin/delete-user", response_class=HTMLResponse)
async def delete_user_form(
    id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        delete_user(db, id)
        return RedirectResponse("/admin/users", status_code=303)
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting user")

# ✅ Список курсов
@router.get("/admin/courses-admin", response_class=HTMLResponse)
async def list_courses_admin(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Проверка прав администратора
        user = await get_current_user(request, db)
        if not user or user.role != RoleEnum.ADMIN:
            return RedirectResponse("/login", status_code=302)
        
        courses = get_all_courses(db)
        return templates.TemplateResponse(
            "admin_course_list.html",
            {
                "request": request,
                "courses": courses
            }
        )
    except Exception as e:
        print(f"Error in list_courses_admin: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/admin/delete-course", response_class=HTMLResponse)
async def delete_course_form(
    id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        delete_course(db, id)
        return RedirectResponse("/admin/courses-admin", status_code=303)
    except Exception as e:
        print(f"Error deleting course: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting course")

# ✅ Форма добавления/редактирования курса
@router.get("/admin/course-form", response_class=HTMLResponse)  # Исправленный путь
async def show_course_form(
    request: Request,
    id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        await verify_admin_access(request, db)
        course = find_course_by_id(db, id) if id else CourseCreate(
            title="", description="", duration=0, price=0.0, 
            category="", status="ACTIVE", image="", instructor_id=None
        )
        instructors = find_teachers(db)
        return templates.TemplateResponse(
            "admin_course_form.html",  # Убедитесь, что шаблон имеет это имя
            {"request": request, "course": course, "instructors": instructors}
        )
    except HTTPException:
        return RedirectResponse("/login", status_code=302)
    except Exception as e:
        logger.error(f"Error in show_course_form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500)

# @router.post("/admin/save-course", response_class=HTMLResponse)  # Измененный путь для единообразия
# async def save_course_form(
#     request: Request,
#     db: Session = Depends(get_db),
#     id: str = Form(None),
#     title: str = Form(...),
#     description: str = Form(""),
#     duration: int = Form(...),
#     price: float = Form(...),
#     category: str = Form(...),
#     status: str = Form(...),
#     image: str = Form(""),
#     instructor_id: Optional[int] = Form(None),
# ):
#     try:
#         await verify_admin_access(request, db)
        
#         course_data = CourseCreate(
#             title=title,
#             description=description,
#             duration=duration,
#             price=price,
#             category=category,
#             status=status,
#             image=image,
#             instructor_id=instructor_id
#         )

#         if id and course_exists(db, id):
#             logger.info(f"Обновление курса с ID: {id}")
#             update_course(db, id, course_data)
#         else:
#             logger.info(f"Создание нового курса: {title}")
#             add_course(db, course_data)

#         return RedirectResponse("/admin/courses-admin", status_code=303)
#     except HTTPException:
#         return RedirectResponse("/login", status_code=302)
#     except Exception as e:
#         logger.error(f"Error in save_course_form: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500)

@router.post("/admin/save-course", response_class=HTMLResponse)
async def save_course_form(
    request: Request,
    db: Session = Depends(get_db),
    id: str = Form(None),
    title: str = Form(...),
    description: str = Form(...),
    duration: int = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    status: str = Form(...),
    image: str = Form(...),
    instructor_id: Optional[int] = Form(None),
):
    try:
        await verify_admin_access(request, db)
        
        # Преобразуем id в int, если он есть
        course_id = int(id) if id and id.strip() else None
        
        # Проверяем преподавателя, если он указан
        instructor = None
        if instructor_id:
            instructor = db.query(User).get(instructor_id)
            if not instructor or instructor.role != RoleEnum.TEACHER:
                raise HTTPException(
                    status_code=400,
                    detail="Указанный пользователь не является преподавателем"
                )

        course_data = CourseCreate(
            title=title,
            description=description,
            duration=duration,
            price=price,
            category=category,
            status=status,
            image=image,
            instructor_id=instructor_id
        )

        if course_id and course_exists(db, course_id):
            logger.info(f"Обновление курса с ID: {course_id}")
            update_course(db, course_id, course_data)
        else:
            logger.info(f"Создание нового курса: {title}")
            add_course(db, course_data)

        return RedirectResponse("/admin/courses-admin", status_code=303)
        
    except HTTPException as he:
        raise he
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in save_course_form: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")