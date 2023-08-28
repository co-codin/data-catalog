from pydantic import BaseModel


class LogIn(BaseModel):
    type: str
    log_name: str
    text: str
    identity_id: str
    event: str
    properties: str | None = None
