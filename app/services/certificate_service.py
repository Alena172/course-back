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
    
    # Регистрируем шрифты
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Получаем текущую директорию
    fonts_dir = os.path.join(r"C:\Бэк_купсач\course_v1\static\fonts") # Создаем путь к директории шрифтов
# Регистрируем шрифты
    pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(fonts_dir, 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(fonts_dir, 'DejaVuSans-Bold.ttf')))
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Фон сертификата (светлый узор)
    p.setFillColorRGB(0.98, 0.98, 0.98)  # Очень светлый серый
    p.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Декоративная рамка
    p.setStrokeColorRGB(0.2, 0.4, 0.6)  # Темно-синий цвет
    p.setLineWidth(3)
    p.rect(30, 30, width-60, height-60, fill=0, stroke=1)
    
    # Улучшенные декоративные элементы в углах (повернутые)
    p.setLineWidth(1.5)
    corner_size = 25
    # Левый верхний
    p.line(30, height-30-corner_size, 30, height-30)
    p.line(30, height-30, 30+corner_size, height-30)
    # Правый верхний
    p.line(width-30-corner_size, height-30, width-30, height-30)
    p.line(width-30, height-30, width-30, height-30-corner_size)
    # Левый нижний
    p.line(30, 30, 30, 30+corner_size)
    p.line(30, 30, 30+corner_size, 30)
    # Правый нижний
    p.line(width-30-corner_size, 30, width-30, 30)
    p.line(width-30, 30, width-30, 30+corner_size)

    # Название организации (меньший размер)
    p.setFillColorRGB(0.2, 0.4, 0.6)
    p.setFont('DejaVuSans-Bold', 12)  # Уменьшен с 14 до 12
    p.drawString(50, height-50, "ОБРАЗОВАТЕЛЬНЫЙ КУРС")

    # Заголовок сертификата
    p.setFillColorRGB(0.8, 0.2, 0.2)  # Красный цвет
    p.setFont('DejaVuSans-Bold', 32)
    p.drawCentredString(width/2, height-150, "СЕРТИФИКАТ")
    
    # Номер сертификата
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.setFont('DejaVuSans', 10)
    p.drawRightString(width-50, height-50, f"№ {datetime.now().strftime('%Y%m%d')}-{user.id}")

    # Основной текст
    p.setFillColorRGB(0, 0, 0)  # Черный цвет
    p.setFont('DejaVuSans', 16)
    p.drawCentredString(width/2, height-210, "Настоящим удостоверяется, что")
    
    # Имя получателя с подчеркиванием
    name = f"{user.name} {user.surname}"
    p.setFillColorRGB(0.1, 0.3, 0.5)  # Темно-синий
    p.setFont('DejaVuSans-Bold', 22)
    text_width = p.stringWidth(name, 'DejaVuSans-Bold', 22)
    p.drawCentredString(width/2, height-250, name)
    # Подчеркивание
    p.setStrokeColorRGB(0.1, 0.3, 0.5)
    p.setLineWidth(1.2)
    p.line(width/2 - text_width/2 - 5, height-255, width/2 + text_width/2 + 5, height-255)

    # Описание достижения
    p.setFillColorRGB(0, 0, 0)
    p.setFont('DejaVuSans', 16)
    p.drawCentredString(width/2, height-290, "успешно завершил(а) курс обучения")
    p.setFont('DejaVuSans-Bold', 20)
    p.setFillColorRGB(0.8, 0.2, 0.2)  # Красный
    p.drawCentredString(width/2, height-320, f"«{course.title}»")

    # Детали курса
    p.setFillColorRGB(0.3, 0.3, 0.3)
    p.setFont('DejaVuSans', 14)
    p.drawCentredString(width/2, height-370, f"Продолжительность: {course.duration} месяцев")
    p.drawCentredString(width/2, height-400, f"Дата выдачи: {datetime.now().strftime('%d.%m.%Y')}")

    # Подпись и печать
    p.setFont('DejaVuSans', 12)
    p.drawString(100, 120, "Директор образовательного центра:")
    p.drawString(100, 100, "_________________________")
    p.drawString(100, 80, "М.П.")  # Место печати

    # Декоративный элемент внизу
    # p.setStrokeColorRGB(0.2, 0.4, 0.6)
    # p.setLineWidth(1)
    # p.line(width/2-100, 60, width/2+100, 60)

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
