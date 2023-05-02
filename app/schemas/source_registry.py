from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, validator

from app.models.sources import Origin, WorkingMode, Status


class CommentIn(BaseModel):
    msg: str

    class Config:
        orm_mode = True


class SourceRegistryCommon(BaseModel):
    name: str
    origin: Origin
    owner: str
    desc: Optional[str] = None


class SourceRegistryIn(SourceRegistryCommon):
    conn_string: str
    working_mode: WorkingMode
    tags: Optional[List[str]] = []

    @validator('conn_string')
    def conn_string_must_be_formatted(cls, v: str):
        driver = v.split('://', maxsplit=1)
        if len(driver) != 2:
            raise ValueError('conn_string field must contain driver')
        return v


class SourceRegistryUpdateIn(SourceRegistryIn):
    synchronized_at: Optional[datetime] = None


class TagOut(BaseModel):
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


class SourceRegistryOutCommon(BaseModel):
    guid: str
    type: str
    status: Status


class SourceRegistryOut(SourceRegistryOutCommon, SourceRegistryUpdateIn):
    created_at: datetime
    updated_at: datetime

    tags: List[TagOut] = []
    comments: List[CommentOut] = []

    class Config:
        orm_mode = True


class SourceRegistryManyOut(SourceRegistryOutCommon, SourceRegistryCommon):
    synchronized_at: Optional[datetime] = None

    tags: List[TagOut] = []
    comments: List[CommentIn] = []

    class Config:
        orm_mode = True
