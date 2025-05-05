from pydantic import BaseModel
from enum import Enum


class BlockType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"

class BlockBase(BaseModel):
    title: str
    content: str
    type: BlockType
    lesson_id: int

class BlockCreate(BlockBase):
    pass

class BlockRead(BlockBase):
    id: int

    model_config = {
        "from_attributes": True
    }
