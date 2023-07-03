from pydantic import BaseModel, Field
from typing import Optional, List


class ModelRelationIn(BaseModel):
    model_version_id: int = Field()
    name: str = Field(..., max_length=200)
    owner: str = Field(..., max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = []
    operation_id: int = Field()


class ModelRelationUpdateIn(BaseModel):
    name: str = Field(None, max_length=200)
    owner: str = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    operation_id: Optional[int] = Field()
