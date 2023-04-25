from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel

from app.models.sources import Origin, WorkingMode, Status


class CommentIn(BaseModel):
    msg: str


class SourceRegistryCommon(BaseModel):
    name: str
    type: str
    origin: Origin
    status: Status
    conn_string: str
    working_mode: WorkingMode
    owner: str
    desc: Optional[str] = None


class SourceRegistryUpdateIn(SourceRegistryCommon):
    synchronized_at: Optional[datetime] = None


class SourceRegistryIn(SourceRegistryCommon):
    tags: Optional[List[str]] = []
    comments: Optional[List[CommentIn]] = []


class TagOut(BaseModel):
    id: int
    name: str

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


class SourceRegistryOut(SourceRegistryUpdateIn):
    _id: int
    guid: str
    created_at: datetime
    updated_at: datetime

    tags: List[TagOut] = []
    comments: List[CommentOut] = []

    class Config:
        orm_mode = True
