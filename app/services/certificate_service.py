import os
from sqlalchemy.orm import Session
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.user import User
from app.schemas.certificate import CertificateCreate
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def generate_certificate_pdf(course, user):
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(r"C:\Бэк_купсач\course_v1\static\fonts")
    pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(fonts_dir, 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(fonts_dir, 'DejaVuSans-Bold.ttf')))
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFillColorRGB(0.98, 0.98, 0.98)
    p.rect(0, 0, width, height, fill=1, stroke=0)
    
    p.setStrokeColorRGB(0.2, 0.4, 0.6) 
    p.setLineWidth(3)
    p.rect(30, 30, width-60, height-60, fill=0, stroke=1)

    p.setLineWidth(1.5)
    corner_size = 25
    p.line(30, height-30-corner_size, 30, height-30)
    p.line(30, height-30, 30+corner_size, height-30)
    p.line(width-30-corner_size, height-30, width-30, height-30)
    p.line(width-30, height-30, width-30, height-30-corner_size)
    p.line(30, 30, 30, 30+corner_size)
    p.line(30, 30, 30+corner_size, 30)
    p.line(width-30-corner_size, 30, width-30, 30)
    p.line(width-30, 30, width-30, 30+corner_size)

    p.setFillColorRGB(0.2, 0.4, 0.6)
    p.setFont('DejaVuSans-Bold', 12) 
    p.drawString(50, height-50, "ОБРАЗОВАТЕЛЬНЫЙ КУРС")

    p.setFillColorRGB(0.8, 0.2, 0.2)
    p.setFont('DejaVuSans-Bold', 32)
    p.drawCentredString(width/2, height-150, "СЕРТИФИКАТ")
    
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.setFont('DejaVuSans', 10)
    p.drawRightString(width-50, height-50, f"№ {datetime.now().strftime('%Y%m%d')}-{user.id}")

    p.setFillColorRGB(0, 0, 0)
    p.setFont('DejaVuSans', 16)
    p.drawCentredString(width/2, height-210, "Настоящим удостоверяется, что")
    
    name = f"{user.name} {user.surname}"
    p.setFillColorRGB(0.1, 0.3, 0.5)
    p.setFont('DejaVuSans-Bold', 22)
    text_width = p.stringWidth(name, 'DejaVuSans-Bold', 22)
    p.drawCentredString(width/2, height-250, name)
    p.setStrokeColorRGB(0.1, 0.3, 0.5)
    p.setLineWidth(1.2)
    p.line(width/2 - text_width/2 - 5, height-255, width/2 + text_width/2 + 5, height-255)

    p.setFillColorRGB(0, 0, 0)
    p.setFont('DejaVuSans', 16)
    p.drawCentredString(width/2, height-290, "успешно завершил(а) курс обучения")
    p.setFont('DejaVuSans-Bold', 20)
    p.setFillColorRGB(0.8, 0.2, 0.2)
    max_width = width - 200  
    words = course.title.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if p.stringWidth(test_line, 'DejaVuSans-Bold', 20) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    y = height - 320
    line_spacing = 24
    y = height - 320
    line_spacing = 24
    for i, line in enumerate(lines):
        if i == 0:
            line = f"«{line}"
        if i == len(lines) - 1:
            line = f"{line}»"
        p.drawCentredString(width / 2, y, line)
        y -= line_spacing

    p.setFillColorRGB(0.3, 0.3, 0.3)
    p.setFont('DejaVuSans', 14)
    p.drawCentredString(width/2, height-370, f"Продолжительность: {course.duration} месяцев")
    p.drawCentredString(width/2, height-400, f"Дата выдачи: {datetime.now().strftime('%d.%m.%Y')}")

    p.setFont('DejaVuSans', 12)
    p.drawString(100, 120, "Директор образовательного центра:")
    p.drawString(100, 100, "_________________________")
    p.drawString(100, 80, "М.П.") 

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
