from pydantic import BaseModel


class MigrationPattern(BaseModel):
    pk_pattern: str = "hash_key"

    fk_table: str = f"^(\w+)$"
    fk_pattern: str = f"^(?:id)?(\w*)_hash_fkey$"


class FieldToCreate(BaseModel):
    is_key: bool | None
    name: str
    db_type: str | None


class FieldToAlter(BaseModel):
    is_key: bool | None
    name: str
    old_type: str | None
    new_type: str | None


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
