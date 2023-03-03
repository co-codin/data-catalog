from pydantic import BaseModel


class NodeIn(BaseModel):
    db: str
    desc: str
    name: str
