from pydantic import BaseModel, Field
from typing import Optional, List, Any


class ModelRelationOperationParameterIn(BaseModel):
    operation_body_parameter_id: int = Field()
    model_resource_attribute_id: Optional[int] = Field(None)
    value: Optional[str] = Field(None)
    model_relation_operation: Optional[Any] = Field(None)


class ModelRelationOperationIn(BaseModel):
    operation_body_id: int = Field()
    model_relation_operation_parameter: list[ModelRelationOperationParameterIn] = Field()


class ModelRelationIn(BaseModel):
    model_version_id: int = Field()
    name: str = Field(..., max_length=200)
    owner: str = Field(..., max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = []
    model_relation_operation: ModelRelationOperationIn = Field()


class ModelRelationOperationParameterUpdateIn(BaseModel):
    model_relation_operation_parameter_id: Optional[int] = Field(None)
    operation_body_parameter_id: Optional[int] = Field(None)
    model_resource_attribute_id: Optional[int] = Field(None)
    value: Optional[str] = Field(None)
    model_relation_operation: Optional[Any] = Field(None)


class ModelRelationOperationUpdateIn(BaseModel):
    model_relation_operation_id: Optional[int] = Field(None)
    operation_body_id: Optional[int] = Field(None)
    model_relation_operation_parameter: list[ModelRelationOperationParameterUpdateIn] = Field()


class ModelRelationUpdateIn(BaseModel):
    name: str = Field(None, max_length=200)
    owner: str = Field(None, max_length=36 * 4)
    desc: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    model_relation_operation: ModelRelationOperationUpdateIn = Field(None)
