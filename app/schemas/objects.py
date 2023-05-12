from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.sources import Origin, Status
from app.schemas.source_registry import CommentIn, TagOut


class ObjectCommon(BaseModel):
    owner: str = Field(..., max_length=36*4)
    short_desc: Optional[str] = None
    business_desc: Optional[str] = None


class ObjectIn(ObjectCommon):
    name: str
    source_registry_guid: str

    tags: Optional[List[str]] = []


class SourceManyOut(BaseModel):
    guid: str
    name: str
    type: str
    origin: Origin
    status: Status

    class Config:
        orm_mode = True


class ObjectManyOut(ObjectCommon):
    guid: str
    name: str
    is_synchronized: bool
    synchronized_at: Optional[datetime] = None
    source: SourceManyOut

    tags: List[TagOut] = []
    comments: List[CommentIn] = []

    class Config:
        orm_mode = True


class CommentOut(CommentIn):
    id: int
    author_guid: str

    author_first_name: Optional[str] = None
    author_last_name: Optional[str] = None
    author_middle_name: Optional[str] = None
    author_email: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class SourceOut(SourceManyOut):
    guid: str
    owner: str
    synchronized_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ObjectOut(ObjectCommon):
    guid: str
    name: str
    is_synchronized: bool
    synchronized_at: Optional[datetime] = None
    local_updated_at: datetime
    source_updated_at: Optional[datetime] = None
    source_created_at: Optional[datetime] = None

    source: SourceOut

    tags: List[TagOut]
    comments: List[CommentOut]

    class Config:
        orm_mode = True


class ObjectUpdateIn(ObjectCommon):
    tags: Optional[List[str]] = []

