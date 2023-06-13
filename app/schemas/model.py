from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.comment import CommentIn, CommentOut
from app.schemas.model_version import ModelVersionOut, ModelVersionManyOut
from app.schemas.tag import TagOut


class ModelCommon(BaseModel):
    name: str = Field(..., max_length=100)
    short_desc: str | None = Field(None, max_length=500)
    business_desc: str | None = Field(None, max_length=500)
    tags: list[str] = []


class ModelIn(ModelCommon):
    owner: str = Field(..., max_length=36*4)


class ModelUpdateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=36*4)
    short_desc: Optional[str] = None
    business_desc: Optional[str] = None
    tags: Optional[List[str]] = None


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

    class Config:
        orm_mode = True


class ModelOut(BaseModel):
    id: int
    guid: str
    source_registry_id: int

    name: str
    owner: str
    short_desc: str | None
    business_desc: str | None

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []
    comments: list[CommentOut] = []
    model_versions: list[ModelVersionManyOut] = []

    class Config:
        orm_mode = True
