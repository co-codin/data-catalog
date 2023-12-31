from __future__ import annotations

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime

from app.enums.enums import Cardinality
from app.schemas.access_label import AccessLabelIn
from app.schemas.tag import TagOut


class ResourceAttributeIn(BaseModel):
    resource_id: int
    name: str = Field(None, max_length=200)
    key: Optional[bool] = Field(None)
    db_link: Optional[str] = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    model_resource_id: Optional[int] = Field(None)
    model_data_type_id: Optional[int] = Field(None)
    cardinality: Optional[Cardinality]
    parent_id: Optional[int] = Field(None)
    tags: Optional[List[str]] = []
    additional: Optional[str] = Field(None)
    access_label: Optional[AccessLabelIn] = None


class ResourceAttributeUpdateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    key: Optional[bool] = Field(None)
    db_link: Optional[str] = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    model_resource_id: Optional[int] = Field(None)
    model_data_type_id: Optional[int] = Field(None)
    cardinality: Optional[str] = Field(None)
    parent_id: Optional[int] = Field(None)
    tags: Optional[List[str]] = Field(None)
    additional: Optional[str] = Field(None)
    access_label: Optional[AccessLabelIn] = None

    @validator('cardinality')
    def cardinality_validator(cls, v):
        accepted = ["0..1", "1..1", "1..*", "0..*"]
        if v and (v not in accepted):
            raise ValueError('Invalid cardinality')

        return v


class ModelResourceAttributeOut(BaseModel):
    id: int
    guid: str

    name: str
    key: str | None
    db_link: str | None
    desc: str | None = None

    resource_id: int
    model_resource_id: int | None
    model_data_type_id: int | None

    cardinality: str | None

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []
    access_label: Any | None

    parent_id: int | None
    additional: str | None
    parents: list[ModelResourceAttributeOut] = []

    model_data_types: Any
    model_resources: Any
    resources: Any

    data_type_errors: str | None
    db_link_error: bool = False

    class Config:
        orm_mode = True


class ModelResourceAttrOutRelIn(BaseModel):
    name: str
    type: str | None = None
    key: bool
