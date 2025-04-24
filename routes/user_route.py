from fastapi import APIRouter, Cookie, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from auth.auth_handler import create_access_token, decode_token, verify_password
from database import get_db
from schemas.user import UserCreate
from services import enrollment_service, user_service
from models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login")
def get_registration_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request, "userReg": {}})


# @router.post("/login")
# def login(
#     request: Request,
#     response: RedirectResponse,
#     email: str = Form(...),
#     password: str = Form(...),
#     db: Session = Depends(get_db),
# ):
#     user = user_service.get_user_by_email(db, email)
#     if user and verify_password(password, user.password):
#         response = RedirectResponse(url="/myaccount", status_code=HTTP_302_FOUND)
#         # ВРЕМЕННО сохраняем email в сессии request.state
#         request.session["user_email"] = email
#         return response
#     return templates.TemplateResponse("form.html", {
#         "request": request,
#         "error": "Неверный email или пароль"
#     })


@router.post("/reg")
def register_user(
    request: Request,
    name: str = Form(...),
    surname: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    confirmPassword: str = Form(...),
    db=Depends(get_db)
):
    if password != confirmPassword:
        return templates.TemplateResponse("form.html", {
            "request": request,
            "userReg": {
                "name": name,
                "surname": surname,
                "email": email,
                "phone": phone
            },
            "error": "Пароли не совпадают"
        })

    user_data = UserCreate(
        name=name,
        surname=surname,
        email=email,
        phone=phone,
        password=password,
        role="STUDENT"
    )
    try:
        user_service.create_user(db, user_data)
    except Exception as e:
        return templates.TemplateResponse("form.html", {
            "request": request,
            "userReg": user_data.dict(),
            "error": str(e)
        })

    return RedirectResponse("/login", status_code=HTTP_302_FOUND)


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = user_service.get_user_by_email(db, email)
    if user and verify_password(password, user.password):
        access_token = create_access_token({"sub": user.email}, user.role)
        response = RedirectResponse(url="/myaccount", status_code=HTTP_302_FOUND)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",  # Добавляем 'Bearer '
            httponly=True,
            secure=True,  # Для HTTPS
            samesite='lax'
        )
        return response
    return templates.TemplateResponse("form.html", {
        "request": request,
        "error": "Неверный email или пароль"
    })


@router.get("/myaccount", response_class=HTMLResponse)
def show_my_account(
    request: Request,
    db: Session = Depends(get_db),
    access_token: str = Cookie(default=None),
):
    print("Access token:", access_token)  # Отладочная печать
    
    if not access_token:
        print("No token found")
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    email = decode_token(access_token)
    print("Decoded email:", email)  # Отладочная печать
    
    if not email:
        print("Invalid or expired token")
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    user = user_service.get_user_by_email(db, email)
    print(f"Retrieved user type: {type(user)}")  # Добавьте эту строку
    if not user:
        print("User not found")
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    enrollments = enrollment_service.find_enrollments_by_student(db, user)
    for enrollment in enrollments:
        completion = enrollment_service.calculate_course_completion(db, user, enrollment.course)
        enrollment.progress = round(completion)

    return templates.TemplateResponse("myaccount.html", {
        "request": request,
        "user": user,
        "enrollments": enrollments
    })


