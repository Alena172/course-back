from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.certificate import CertificateCreate, CertificateRead
from app.services import certificate_service
from app.auth.auth_bearer import JWTBearer
from app.auth.role_checker import RoleChecker

router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"],
    dependencies=[Depends(JWTBearer()), Depends(RoleChecker(["Student"]))]
)

@router.post("/", response_model=CertificateRead)
def issue_certificate(cert: CertificateCreate, db: Session = Depends(get_db)):
    return certificate_service.create_certificate(db, cert)

@router.get("/user/{user_id}", response_model=list[CertificateRead])
def get_user_certificates(user_id: int, db: Session = Depends(get_db)):
    return certificate_service.get_certificates_by_user(db, user_id)

