from pydantic import BaseModel


class FieldToCreate(BaseModel):
    is_key: bool | None
    name: str
    db_type: str


class FieldToAlter(BaseModel):
    is_key: bool | None
    name: str
    old_type: str
    new_type: str


class TableToCreate(BaseModel):
    name: str
    db: str
    fields: list[FieldToCreate] = []


class TableToAlter(BaseModel):
    name: str
    fields_to_create: list[FieldToCreate] = []
    fields_to_alter: list[FieldToAlter] = []
    fields_to_delete: list[str] = []


class SchemaOut(BaseModel):
    name: str
    tables_to_create: list[TableToCreate] = []
    tables_to_alter: list[TableToAlter] = []
    tables_to_delete: list[str] = []


class MigrationOut(BaseModel):
    name: str
    schemas: list[SchemaOut] = []
