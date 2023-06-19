from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

from app.schemas.tag import TagOut


class OperationParameterIn(BaseModel):
    flag: bool = Field(...)
    name: str = Field(..., max_length=200)
    name_for_relation: str = Field(..., max_length=200)
    model_data_type_id: int = Field(...)


class OperationIn(BaseModel):
    name: str = Field(..., max_length=200)
    owner: str = Field(..., max_length=36 * 4)
    status: str = Field(..., max_length=50)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    code: str = Field(...)
    parameters: list[OperationParameterIn] = []


class OperationBodyParametersManyOut(BaseModel):
    id: int
    guid: str

    flag: bool
    name: str
    name_for_relation: str
    model_data_type_id: int

    class Config:
        orm_mode = True


class OperationBodyOut(BaseModel):
    id: int
    guid: str

    code: str
    operation_body_parameters = OperationBodyParametersManyOut

    class Config:
        orm_mode = True


class OperationOut(BaseModel):
    id: int
    guid: str

    name: str
    owner: str
    status: str
    desc: str | None

    created_at: datetime
    updated_at: datetime

    tags: list[TagOut] = []
    operation_body: list[OperationBodyOut] = []

    class Config:
        orm_mode = True


class OperationUpdateIn(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    owner: Optional[str] = Field(None, max_length=36 * 4)
    status: Optional[str] = Field(None, max_length=50)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    code: Optional[str] = None
    parameters: Optional[list[OperationParameterIn]] = None
