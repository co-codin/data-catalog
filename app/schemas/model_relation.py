from pydantic import BaseModel, Field
from typing import Optional, List


class ModelRelationIn(BaseModel):
    model_relation_group_id: int = Field()
    name: str = Field(..., max_length=200)
    owner: str = Field(..., max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = []
    function: Optional[str] = Field(None, max_length=500)


class ModelRelationUpdateIn(BaseModel):
    name: str = Field(None, max_length=200)
    owner: str = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    function: Optional[str] = Field(None, max_length=500)
