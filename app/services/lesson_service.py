import logging
from sqlalchemy.orm import Session
from app.models.lesson import Lesson
from app.models.course import Course
from app.models.block import Block, BlockType
from app.services.block_service import delete_blocks_by_lesson, save_all_blocks
from typing import List


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def find_by_id(db: Session, lesson_id: int) -> Lesson:
    lesson = db.query(Lesson).filter_by(id=lesson_id).first()
    if not lesson:
        raise RuntimeError("Lesson not found")
    return lesson


def find_lessons_by_course(db: Session, course_id: int) -> List[Lesson]:
    return db.query(Lesson).filter_by(course_id=course_id).all()


def save_lesson(db: Session, lesson_data: dict, lesson_id: int = None):
    """Создать или обновить урок"""
    try:
        if lesson_id:
            lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
            if not lesson:
                raise ValueError("Урок не найден")
            lesson.title = lesson_data["title"]
            db.query(Block).filter(Block.lesson_id == lesson_id).delete()
        else:
            lesson = Lesson(
                title=lesson_data["title"],
                course_id=lesson_data["course_id"]
            )
            db.add(lesson)
            db.commit()
            db.refresh(lesson)
        blocks = []
        for block_data in lesson_data.get("blocks", []):
            block = Block(
                title=block_data["title"],
                type=block_data["type"],
                content=block_data["content"],
                lesson_id=lesson.id
            )
            blocks.append(block)
        db.bulk_save_objects(blocks)
        db.commit()
        return lesson
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving lesson: {str(e)}", exc_info=True)
        raise


def delete_lesson_by_id(db: Session, lesson_id: int):
    lesson = find_by_id(db, lesson_id)
    db.delete(lesson)
    db.commit()


def update_blocks(db: Session, lesson: Lesson, block_title: List[str], block_type: List[str], block_content: List[str]):
    blocks = []
    for i in range(len(block_title)):
        block = Block(
            title=block_title[i],
            type=BlockType(block_type[i]),
            content=block_content[i],
            lesson_id=lesson.id
        )
        blocks.append(block)
    delete_blocks_by_lesson(db, lesson.id)
    save_all_blocks(db, blocks)


def save(db: Session, lesson: Lesson) -> Lesson:
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson
