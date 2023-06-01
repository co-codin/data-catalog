import json
import uuid

from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


from app.crud.crud_source_registry import remove_redundant_tags
from app.models import SourceRegister, Object, Field, Status
from app.mq import create_channel
from app.schemas.migration import MigrationOut, FieldToCreate
from app.database import db_session
from app.config import settings


async def send_for_synchronization(source_registry_guid: str, conn_string: str):
    migration_pattern = {
        "pk_pattern": r"_?hash_key",
        "fk_table": r"^(\w+)$",
        "fk_pattern": r"^(?:id)?(\w*)_hash_fkey$"
    }
    db_source = conn_string.rsplit('/', maxsplit=1)[1]
    async with create_channel() as channel:
        await channel.basic_publish(
            exchange=settings.migration_exchange,
            routing_key='task',
            body=json.dumps(
                {
                    'name': f'{datetime.now().strftime("%Y-%m-%d")}.{db_source}',
                    'conn_string': conn_string,
                    'migration_pattern': migration_pattern,
                    'source_registry_guid': source_registry_guid
                }
            )
        )


async def update_data_catalog_data(graph_migration: str):
    graph_migration = json.loads(graph_migration)

    if graph_migration:
        applied_migration = MigrationOut(**graph_migration['graph_migration'])
        source_registry_guid = graph_migration['source_registry_guid']
        conn_string = graph_migration['conn_string']

        async with db_session() as session:
            registry = await session.execute(
                select(SourceRegister)
                .options(selectinload(SourceRegister.objects))
                .where(SourceRegister.guid == source_registry_guid)
            )
            registry = registry.scalars().first()

            db_source = conn_string.rsplit('/', maxsplit=1)[1]

            await add_objects(applied_migration, db_source, registry, session)
            await delete_objects(applied_migration, db_source, session)
            await alter_objects(applied_migration, db_source, registry, session)
            await set_synchronized_at(registry)

            registry.status = Status.ON
            registry.synchronized_at = datetime.now()

            await session.commit()

            await remove_redundant_tags(session)


async def add_objects(
        applied_migration: MigrationOut, db_source: str, source_registry: SourceRegister, session: AsyncSession
):
    objects = await create_objects_from_migration_out(applied_migration, db_source, source_registry.owner)
    source_registry.objects.extend(objects)

    session.add(source_registry)


async def create_objects_from_migration_out(migration: MigrationOut, db_source: str, owner: str) -> list[Object]:
    tables = []
    for schema in migration.schemas:
        for table in schema.tables_to_create:
            object_db_path = f'{db_source}.{schema.name}.{table.name}'
            now = datetime.now()
            guid = str(uuid.uuid4())
            object_ = Object(
                name=table.name, owner=owner, db_path=object_db_path, source_created_at=now, guid=guid,
                source_updated_at=now, local_updated_at=now, synchronized_at=now, is_synchronized=True
            )
            for field in table.fields:
                field_db_path = f'{object_db_path}.{field.name}'
                guid = str(uuid.uuid4())
                field_model = Field(
                    name=field.name, type=field.db_type, guid=guid, is_key=field.is_key, db_path=field_db_path,
                    owner=owner, source_created_at=now, source_updated_at=now, local_updated_at=now,
                    synchronized_at=now, length=len(field.name)
                )
                object_.fields.append(field_model)
            tables.append(object_)
    return tables


async def delete_objects(applied_migration: MigrationOut, db_source: str, session: AsyncSession):
    tables_to_delete = [
        f'{db_source}.{schema.name}.{table}'
        for schema in applied_migration.schemas
        for table in schema.tables_to_delete
    ]
    if tables_to_delete:
        await session.execute(
            delete(Object)
            .where(Object.db_path.in_(tables_to_delete))
        )


async def alter_objects(
        applied_migration: MigrationOut, db_source: str, source_registry: SourceRegister, session: AsyncSession
):
    tables_to_alter = {
        f'{db_source}.{schema.name}.{table.name}'
        for schema in applied_migration.schemas
        for table in schema.tables_to_alter
    }
    object_db_path_to_object: dict[str: Object] = source_registry.object_db_path_to_object(tables_to_alter)
    fields_to_delete = []

    for schema in applied_migration.schemas:
        for table in schema.tables_to_alter:
            table_db_path = f'{db_source}.{schema.name}.{table.name}'
            fields_to_create = await create_fields(table.fields_to_create, table_db_path, source_registry.owner)

            curr_object = object_db_path_to_object[table_db_path]
            curr_object.fields.extend(fields_to_create)

            now = datetime.now()
            curr_object.source_updated_at = now

            fields_to_alter = curr_object.field_db_path_to_field
            for field in table.fields_to_alter:
                field_db_path = f'{table_db_path}.{field.name}'
                field_to_alter_model = fields_to_alter[field_db_path]
                field_to_alter_model.type = field.new_type
                field.source_updated_at = now

            session.add(curr_object)

            for field in table.fields_to_delete:
                field_db_path = f'{table_db_path}.{field}'
                fields_to_delete.append(field_db_path)

    if fields_to_delete:
        await session.execute(
            delete(Field)
            .where(Field.db_path.in_(fields_to_delete))
        )


async def create_fields(fields_to_create: list[FieldToCreate], table_db_path: str, owner: str) -> list[Field]:
    fields = []
    now = datetime.now()
    for field in fields_to_create:
        guid = str(uuid.uuid4())
        field_model = Field(
            name=field.name, type=field.db_type, is_key=field.is_key, guid=guid,
            db_path=f'{table_db_path}.{field.name}', owner=owner, source_created_at=now, source_updated_at=now,
            local_updated_at=now, synchronized_at=now, length=len(field.name)
        )
        fields.append(field_model)
    return fields


async def set_synchronized_at(source_registry: SourceRegister):
    now = datetime.now()
    for object_ in source_registry.objects:
        object_.synchronized_at = now
        for field in object_.fields:
            field.synchronized_at = now
