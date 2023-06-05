from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.sources import Origin, Status
from app.schemas.source_registry import CommentIn, TagOut


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


class FieldManyOut(BaseModel):
    guid: str
    is_key: bool
    name: str
    type: str
    length: int
    owner: str
    desc: str | None

    local_updated_at: datetime
    synchronized_at: datetime | None
    source_updated_at: datetime | None

    tags: list[TagOut] = []
    comments: list[CommentIn] = []

    class Config:
        orm_mode = True


class FieldOut(FieldManyOut):
    source_created_at: datetime | None
    type: str
    db_path: str
    desc: str | None

    comments: list[CommentOut] = []

    class Config:
        orm_mode = True


class FieldUpdateIn(BaseModel):
    owner: str
    desc: str
    tags: list[str] = []


class ObjectManyOut(ObjectCommon):
    guid: str
    name: str
    is_synchronized: bool
    synchronized_at: datetime | None
    source: SourceManyOut

    tags: list[TagOut] = []
    comments: list[CommentIn] = []

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
    db_path: str
    is_synchronized: bool

    synchronized_at: datetime | None
    local_updated_at: datetime
    source_updated_at: datetime | None
    source_created_at: datetime | None

    source: SourceOut

    tags: list[TagOut]
    comments: list[CommentOut]

    class Config:
        orm_mode = True


class ObjectUpdateIn(ObjectCommon):
    tags: Optional[List[str]] = []


class ObjectSynch(BaseModel):
    object_name: str
    conn_string: str
    source_registry_guid: str
