from fastapi import APIRouter, Cookie, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from app.auth.auth_handler import create_access_token, decode_token, verify_password
from app.database import get_db
from app.schemas.user import UserCreate
from app.services import enrollment_service, user_service
from app.models.user import RoleEnum, User

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login")
def get_registration_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request, "userReg": {}})


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
        if user.role == RoleEnum.ADMIN:
            redirect_url = "/admin/dashboard"
        elif user.role == RoleEnum.TEACHER:
            redirect_url = "/teacher/courses"
        else:
            redirect_url = "/myaccount"
            
        response = RedirectResponse(url=redirect_url, status_code=HTTP_302_FOUND)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=True,
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
    print("Access token:", access_token)
    
    if not access_token:
        print("No token found")
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    email = decode_token(access_token)
    print("Decoded email:", email)
    
    if not email:
        print("Invalid or expired token")
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    user = user_service.get_user_by_email(db, email)
    print(f"Retrieved user type: {type(user)}")
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

@router.get("/logout")
async def logout_user(response: Response):
    redirect_response = RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
    # Очищаем куки с access_token
    redirect_response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,  # Для HTTPS
        samesite="lax"
    )
    
    return redirect_response


