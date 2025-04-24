from sqlalchemy.orm import Session
from models.certificate import Certificate
from models.course import Course
from models.user import User
from schemas.certificate import CertificateCreate
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime


def generate_certificate_pdf(course, user):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    width, height = A4
    p.setFont("Helvetica-Bold", 28)
    p.drawCentredString(width / 2, height - 100, "СЕРТИФИКАТ")

    p.setFont("Helvetica", 16)
    p.drawCentredString(width / 2, height - 160, f"Настоящим подтверждается, что")
    
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 190, f"{user.name} {user.surname}")

    p.setFont("Helvetica", 16)
    p.drawCentredString(width / 2, height - 230, f"успешно завершил курс:")
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 260, f"{course.title}")

    p.setFont("Helvetica", 14)
    p.drawCentredString(width / 2, height - 300, f"Длительность: {course.duration} месяцев")
    p.drawCentredString(width / 2, height - 330, f"Дата выдачи: {datetime.now().date()}")

    p.setFont("Helvetica-Oblique", 12)
    p.drawCentredString(width / 2, 100, "Подпись организатора: __________________________")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()


def create_certificate(db: Session, cert: CertificateCreate):
    db_cert = Certificate(**cert.dict())
    db.add(db_cert)
    db.commit()
    db.refresh(db_cert)
    return db_cert

def get_certificates_by_user(db: Session, user_id: int):
    return db.query(Certificate).filter(Certificate.user_id == user_id).all()

def find_by_course_and_user(db: Session, course: Course, user: User):
    return db.query(Certificate).filter(
        Certificate.course_id == course.id,
        Certificate.user_id == user.id
    ).first()
