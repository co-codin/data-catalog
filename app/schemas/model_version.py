from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel, Field

from app.schemas.access_label import AccessLabelIn
from app.schemas.comment import CommentOut
from app.schemas.model_quality import ModelQualityManyOut
from app.schemas.tag import TagOut


class ModelVersionIn(BaseModel):
    model_id: int
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = []
    access_label: Optional[AccessLabelIn] = None
    should_be_cloned: bool


class ModelVersionUpdateIn(BaseModel):
    status: str = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=36*4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    access_label: Optional[AccessLabelIn] = None


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
    access_label: Any | None

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
    tags: list[TagOut] = []
    comments: list[CommentOut] = []
    access_label: Any | None

    created_at: datetime
    updated_at: datetime | None

    class Config:
        orm_mode = True
