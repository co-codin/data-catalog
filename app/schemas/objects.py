from typing import List, Optional
from pydantic import BaseModel, Field


class ObjectIn(BaseModel):
    name: str
    source_registry_guid: str
    owner: str = Field(..., max_length=36*4)
    short_desc: Optional[str] = None
    business_desc: Optional[str] = None

    tags: Optional[List[str]] = []
