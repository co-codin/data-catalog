from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.comment import CommentOut
from app.schemas.model_quality import ModelQualityManyOut
from app.schemas.tag import TagOut


class ModelVersionIn(BaseModel):
    model_id: int
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []


class ModelVersionUpdateIn(BaseModel):
    status: str = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None


class ModelVersionOut(BaseModel):
    id: str
    guid: str
    model_id: int
    owner: str
    desc: str | None
    status: str
    version: str | None

    created_at: datetime
    updated_at: datetime

    model_qualities: list[ModelQualityManyOut] = []
    tags: list[TagOut] = []
    comments: list[CommentOut] = []

    class Config:
        orm_mode = True


class ModelVersionManyOut(BaseModel):
    id: str
    guid: str
    model_id: int
    owner: str
    desc: str | None
    status: str
    version: str | None
    comments: list[CommentOut] = []

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
