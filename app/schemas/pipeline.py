from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

from app.schemas.tag import TagOut


class PipelineIn(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    owner: Optional[str] = Field(None)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    model_version_id: int
    operating_mode: bool = Field(...)
    state: bool = Field(...)
    base: bool = Field(...)


class PipelineUpdateIn(BaseModel):
    owner: Optional[str] = Field(None)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    state: Optional[bool] = Field(None)
    base: Optional[bool] = Field(None)
    model_version_id: Optional[int] = Field(None)
    operating_mode: Optional[bool] = Field(None)
