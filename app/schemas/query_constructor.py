from pydantic import BaseModel, Field
from typing import List, Optional, Any

from app.schemas.model_version import ModelVersionManyOut


class QueryConstructorIn(BaseModel):
    name: str = Field(..., max_length=200)
    owner: str = Field(..., max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    model_version_id: int
    filters: Optional[str] = Field(None)
    aggregators: Optional[str] = Field(None)
    fields: list[int] = []
    tags: Optional[List[str]] = None


class QueryConstructorUpdateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    owner: Optional[str] = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    model_version_id: Optional[int] = Field(None)
    filters: Optional[str] = Field(None)
    aggregators: Optional[str] = Field(None)
    fields: list[int] = None
    tags: Optional[List[str]] = None


class QueryConstructorBodyFieldsManyOut(BaseModel):
    id: int
    guid: str
    model_resource_attribute_id: int

    class Config:
        orm_mode = True


class QueryConstructorBodyOut(BaseModel):
    id: int
    guid: str
    filters: str
    model_version_id: int
    aggregators: str
    model_version: Any

    class Config:
        orm_mode = True


class QueryConstructorManyOut(BaseModel):
    id: int
    guid: str
    name: str
    owner: str
    desc: str | None
    query_constructor_body: list[QueryConstructorBodyOut] = []

    class Config:
        orm_mode = True


class QueryConstructorOut(BaseModel):
    id: int
    guid: str
    name: str
    owner: str
    desc: str | None
    filters: str | None
    aggregators: str | None
    query_constructor_body: list[QueryConstructorBodyOut] = []

    class Config:
        orm_mode = True
