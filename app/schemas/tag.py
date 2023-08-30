from pydantic import BaseModel


class TagOut(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True
