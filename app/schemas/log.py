from typing import Optional

from pydantic import BaseModel, Field


class LogIn(BaseModel):
    type: str
    log_name: str
    text: str
    identity_id: str
    event: str
    description: str
    properties: Optional[str] = Field(None)
