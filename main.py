from fastapi import FastAPI
from routes import (
    admin_route,
    course_route,
    lesson_progress_route,
    user_route,
    lesson_route,
    block_route,
    enrollment_route,
    certificate_route
)
from database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

app.include_router(course_route.router)
app.include_router(user_route.router)
app.include_router(lesson_route.router)
app.include_router(block_route.router)
app.include_router(enrollment_route.router)
app.include_router(lesson_progress_route.router)
app.include_router(certificate_route.router)
app.include_router(admin_route.router)