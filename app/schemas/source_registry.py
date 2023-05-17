from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator

from app.models.sources import Origin, WorkingMode, Status


class CommentIn(BaseModel):
    msg: str = Field(..., max_length=10_000)

    class Config:
        orm_mode = True


class SourceRegistryCommon(BaseModel):
    name: str = Field(..., max_length=100)
    origin: Origin
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)


class SourceRegistryIn(SourceRegistryCommon):
    conn_string: str = Field(..., max_length=500)
    working_mode: WorkingMode
    tags: Optional[List[str]] = []

    @validator('conn_string')
    def conn_string_must_be_formatted(cls, v: str):
        driver = v.split('://', maxsplit=1)
        if len(driver) != 2 or not (driver[0] and driver[1]):
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


class SourceRegistryOut(SourceRegistryOutCommon, SourceRegistryCommon):
    conn_string: str = Field(None, max_length=500)
    working_mode: WorkingMode

    created_at: datetime
    updated_at: datetime
    synchronized_at: Optional[datetime] = None

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
