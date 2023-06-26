from pydantic import BaseModel, Field


class ModelAttitudeIn(BaseModel):
    resource_id: int = Field()
    left_attribute_id: int = Field()
    right_attribute_id: int = Field()

