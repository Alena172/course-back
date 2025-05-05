# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from auth.auth_bearer import JWTBearer
# from auth.role_checker import RoleChecker
# from database import get_db
# from schemas.course import CourseRead
# from services import enrollment_service, course_service

# router = APIRouter(
#     prefix="/myaccount",
#     tags=["My Account"],
#     dependencies=[Depends(RoleChecker(["Student"]))]
# )

# @router.get("/courses", response_model=list[CourseRead])
# def get_my_courses(
#     db: Session = Depends(get_db),
#     payload: dict = Depends(JWTBearer())
# ):
#     user_id = payload["sub"]
#     enrollments = enrollment_service.get_enrollments_by_user(db, user_id)
#     course_ids = [e.course_id for e in enrollments]
#     return course_service.get_courses_by_ids(db, course_ids)
