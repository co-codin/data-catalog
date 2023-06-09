from typing import Optional
from typing import List

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.tag import TagOut
from app.schemas.comment import CommentIn, CommentOut


class ModelQualityIn(BaseModel):
    model_version_id: int = Field()
    name: str = Field(..., max_length=200)
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=1000)
    function: Optional[str] = Field(None)
    tags: Optional[List[str]] = []


class ModelQualityUpdateIn(BaseModel):
    name: str = Field(None, max_length=200)
    owner: str = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    function: Optional[str] = Field(None)
    tags: Optional[List[str]] = None


class ModelQualityOut(ModelQualityIn):
    id: int
    guid: str

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []
    comments: list[CommentOut] = []


class ModelQualityManyOut(ModelQualityOut):
    comments: list[CommentIn] = []
