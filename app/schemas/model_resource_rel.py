from pydantic import BaseModel


class ModelResourceRelOut(BaseModel):
    resource_attr: str
    mapped_resource: str
    mapped_resource_key_attr: str
    gid: int


class ModelResourceRelIn(BaseModel):
    resource_attr: str
    mapped_resource_guid: str
    mapped_resource_key_attr: str
