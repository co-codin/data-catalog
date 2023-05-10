from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.sources import Origin, Status


class ObjectIn(BaseModel):
    name: str
    source_registry_guid: str
    owner: str = Field(..., max_length=36*4)
    short_desc: Optional[str] = None
    business_desc: Optional[str] = None

    tags: Optional[List[str]] = []


class SourceManyOut(BaseModel):
    name: str
    type: str
    origin: Origin
    status: Status

    class Config:
        orm_mode = True


class ObjectManyOut(BaseModel):
    guid: str
    name: str
    owner: str
    synchronized_at: Optional[datetime] = None
    source: SourceManyOut

    class Config:
        orm_mode = True
