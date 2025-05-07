from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import Response
from app.database import get_db
from app.auth.auth_bearer import JWTBearer
from app.routes.course_route import get_current_user
from app.services import enrollment_service, course_service, user_service
from app.services.certificate_service import generate_certificate_pdf
from starlette.responses import StreamingResponse
import io


router = APIRouter(tags=["Enrollment"])

templates = Jinja2Templates(directory="templates")


@router.get("/myaccount", dependencies=[Depends(JWTBearer())])
def show_my_account(request: Request, db: Session = Depends(get_db)):
    user = user_service.get_current_user(request, db)
    enrollments = enrollment_service.get_enrollments_by_user(db, user)

    for enrollment in enrollments:
        progress = enrollment_service.calculate_completion(db, user, enrollment.course)
        enrollment.progress = round(progress)

    return templates.TemplateResponse("myaccount.html", {
        "request": request,
        "user": user,
        "enrollments": enrollments
    })

@router.post("/enroll/{course_id}")
async def enroll_in_course(course_id: int, request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    course = course_service.find_course_by_id(db, course_id)
    if not course:
        return RedirectResponse("/courses", status_code=404)

    existing_enrollment = enrollment_service.find_enrollment(db, user.id, course_id)
    if existing_enrollment:
        return RedirectResponse("/myaccount", status_code=303)
    enrollment_service.enroll_user_in_course(db, user.id, course_id)

    return RedirectResponse("/myaccount", status_code=303)

@router.get("/certificate/{course_id}/{user_id}")
def issue_certificate(course_id: int, user_id: int, db: Session = Depends(get_db)):
    user = user_service.find_user_by_id(db, user_id)
    course = course_service.find_course_by_id(db, course_id)
    enrollment = enrollment_service.find_enrollment(db, user.id, course.id)

    if not enrollment:
        return Response("Запись о прохождении курса не найдена", status_code=404)

    pdf_bytes = generate_certificate_pdf(course, user)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=certificate.pdf"}
    )

