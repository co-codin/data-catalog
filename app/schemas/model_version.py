
from typing import List
from pydantic import Field

from pydantic import BaseModel
from typing import Optional


class ModelVersionIn(BaseModel):
    model_id: int
    name: str = Field(..., max_length=100)
    owner: str = Field(..., max_length=36*4)
    desc: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []
