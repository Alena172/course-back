from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.models.lesson import Lesson
from app.models.user import RoleEnum
from app.routes import (
    admin_route,
    course_route,
    lesson_progress_route,
    user_route,
    lesson_route,
    block_route,
    enrollment_route,
    certificate_route
)
from app.database import Base, engine, get_db
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root_redirect(request: Request, db: Lesson = Depends(get_db)):
    user = await course_route.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    if user.role == RoleEnum.ADMIN:
        return RedirectResponse(url="/admin/dashboard")
    elif user.role == RoleEnum.TEACHER:
        return RedirectResponse(url="/teacher/courses")
    else: 
        return RedirectResponse(url="/myaccount")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/login")

Base.metadata.create_all(bind=engine)

app.include_router(course_route.router)
app.include_router(user_route.router)
app.include_router(lesson_route.router)
app.include_router(block_route.router)
app.include_router(enrollment_route.router)
app.include_router(lesson_progress_route.router)
app.include_router(certificate_route.router)
app.include_router(admin_route.router)