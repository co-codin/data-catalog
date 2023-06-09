from pydantic import BaseModel, Field
from typing import Optional
from typing import List


class ModelQualityIn(BaseModel):
    model_version_id: int = Field()
    name: str = Field(..., max_length=200)
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=1000)
    function: Optional[str] = Field(None)
    tags: Optional[List[str]] = []


class ModelQualityUpdateIn(BaseModel):
    name: str = Field(None, max_length=200)
    owner: str = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    function: Optional[str] = Field(None)
    tags: Optional[List[str]] = None