from datetime import datetime

from pydantic import BaseModel


class LogIn(BaseModel):
    type: str
    log_name: str
    text: str
    identity_id: str
    event: str
    properties: str | None = None

    class Config:
        orm_mode = True


class LogOut(LogIn):
    id: int
    created_at: datetime
    author_first_name: str
    author_last_name: str
    author_middle_name: str | None = None
    author_email: str

    class Config:
        orm_mode = True
