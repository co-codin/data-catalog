from pydantic import BaseModel, Field


class ModelAttitudeIn(BaseModel):
    resource_id: int = Field()
