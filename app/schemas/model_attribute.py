from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
from datetime import datetime

from app.models.models import Cardinality
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

    @validator('cardinality')
    def cardinality_validator(cls, v):
        accepted = ["0..1", "1..1", "1..*", "0..*"]
        if v not in accepted:
            raise ValueError('Invalid cardinality')

        return v


class ModelResourceAttributeOut(BaseModel):
    id: int
    guid: str

    name: str
    key: str | None
    db_link: str| None
    desc: str | None = None

    resource_id: int
    model_resource_id: int | None
    model_data_type_id: int | None

    cardinality: str| None

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []

    parent_id: int | None
    additional: str | None
    parents: list[__name__] = []

    model_data_types: Any
    model_resources: Any
    resources: Any

    class Config:
        orm_mode = True
