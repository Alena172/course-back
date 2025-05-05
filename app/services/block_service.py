from sqlalchemy.orm import Session
from app.models.block import Block
from typing import List


def save_block(db: Session, block: Block) -> Block:
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


def find_blocks_by_lesson(db: Session, lesson_id: int) -> List[Block]:
    return db.query(Block).filter_by(lesson_id=lesson_id).all()


def save_all_blocks(db: Session, blocks: List[Block]) -> List[Block]:
    db.add_all(blocks)
    db.commit()
    return blocks


def find_block_by_id(db: Session, block_id: int) -> Block:
    block = db.query(Block).filter_by(id=block_id).first()
    if not block:
        raise RuntimeError(f"Block not found with id: {block_id}")
    return block


def delete_block(db: Session, block_id: int):
    block = find_block_by_id(db, block_id)
    db.delete(block)
    db.commit()


def delete_blocks_by_lesson(db: Session, lesson_id: int):
    blocks = find_blocks_by_lesson(db, lesson_id)
    for block in blocks:
        db.delete(block)
    db.commit()
