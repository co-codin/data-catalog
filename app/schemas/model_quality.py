from pydantic import BaseModel, Field
from typing import Optional
from typing import List


class ModelQualityIn(BaseModel):
    model_version_id: int = Field()
    name: str = Field(..., max_length=100)
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)
    function: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []


class ModelQualityUpdateIn(BaseModel):
    status: str = Field(None, max_length=100)
    owner: Optional[str] = Field(None, max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []