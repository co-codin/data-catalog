from datetime import datetime

from pydantic import BaseModel, Field


class CommentIn(BaseModel):
    msg: str = Field(..., max_length=10_000)

    class Config:
        orm_mode = True


class CommentOut(CommentIn):
    id: int
    author_guid: str

    author_first_name: str | None
    author_last_name: str | None
    author_middle_name: str | None
    author_email: str | None

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
