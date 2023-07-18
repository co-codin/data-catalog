from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel, Field

from app.schemas.access_label import AccessLabelIn
from app.schemas.comment import CommentIn, CommentOut
from app.schemas.model_version import ModelVersionManyOut
from app.schemas.tag import TagOut


class ModelCommon(BaseModel):
    name: str = Field(..., max_length=100)
    short_desc: str | None = Field(None, max_length=200)
    business_desc: str | None = Field(None, max_length=2000)
    tags: list[str] = []


class ModelIn(ModelCommon):
    owner: str = Field(..., max_length=36*4)
    access_label: Optional[AccessLabelIn] = None


class ModelUpdateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=36*4)
    short_desc: Optional[str] = Field(None, max_length=200)
    business_desc: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = None
    access_label: Optional[AccessLabelIn] = None


class ModelManyOut(BaseModel):
    id: int
    guid: str
    source_registry_id: int | None

    name: str
    owner: str
    short_desc: str | None
    business_desc: str | None

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []
    comments: list[CommentIn] = []
    access_label: Any | None

    class Config:
        orm_mode = True


class ModelOut(BaseModel):
    id: int
    guid: str
    source_registry_id: int | None

    name: str
    owner: str
    short_desc: str | None
    business_desc: str | None

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []
    comments: list[CommentOut] = []
    model_versions: list[ModelVersionManyOut] = []
    access_label: Any | None

    class Config:
        orm_mode = True
