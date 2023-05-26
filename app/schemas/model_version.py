
from typing import List
from pydantic import Field

from pydantic import BaseModel
from typing import Optional


class ModelVersionIn(BaseModel):
    model_id: int
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []


class ModelVersionUpdateIn(BaseModel):
    model_id: Optional[int] = None
    version: Optional[str] = Field(None, max_length=500)
    owner: Optional[str] = Field(None, max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = []