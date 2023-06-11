from pydantic import BaseModel


class TagOut(BaseModel):
    name: str

    class Config:
        orm_mode = True
