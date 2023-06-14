import json
import uuid

from datetime import datetime
from enum import Enum

from sqlalchemy import select, delete, update, and_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession


from app.crud.crud_tag import remove_redundant_tags
from app.models import (
    SourceRegister, Object, Field, Status, Model, ModelVersion, ModelResource, ModelResourceAttribute, Cardinality
)
from app.mq import create_channel
from app.schemas.migration import MigrationOut, FieldToCreate, MigrationPattern
from app.schemas.model import ModelCommon
from app.database import db_session
from app.constants.data_types import SYS_DATA_TYPE_TO_ID
from app.config import settings


class MigrationRequestStatus(Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'


async def send_for_synchronization(
        source_registry_guid: str, conn_string: str, migration_pattern: MigrationPattern,
        model_in: ModelCommon = None, object_name: str = None
):
    db_source = conn_string.rsplit('/', maxsplit=1)[1]

    if object_name:
        migration_name = f'{datetime.now().strftime("%Y-%m-%d")}.{db_source}.{object_name}'
    else:
        migration_name = f'{datetime.now().strftime("%Y-%m-%d")}.{db_source}'

    params = {
        'name': migration_name,
        'conn_string': conn_string,
        'migration_pattern': migration_pattern.dict(),
        'source_registry_guid': source_registry_guid,
        'object_name': object_name,
        'model': model_in.dict() if model_in else None
    }

    async with create_channel() as channel:
        await channel.basic_publish(
            exchange=settings.migration_exchange,
            routing_key='task',
            body=json.dumps(params)
        )


async def update_data_catalog_data(graph_migration: str):
    graph_migration = json.loads(graph_migration)
    match graph_migration['status']:
        case MigrationRequestStatus.SUCCESS.value:
            await process_graph_migration_success(graph_migration)
        case MigrationRequestStatus.FAILURE.value:
            await process_graph_migration_failure(graph_migration)


async def process_graph_migration_success(graph_migration: dict):
    if graph_migration:
        applied_migration = MigrationOut(**graph_migration['graph_migration'])
        source_registry_guid = graph_migration['source_registry_guid']
        conn_string = graph_migration['conn_string']
        object_name = graph_migration['object_name']
        model_in = graph_migration['model']

        async with db_session() as session:
            registry = await get_source_registry(source_registry_guid, session)
            db_source = conn_string.rsplit('/', maxsplit=1)[1]

            if model_in:
                model = Model(**model_in, guid=str(uuid.uuid4()), owner=registry.owner)
                model_version = ModelVersion(guid=str(uuid.uuid4()), owner=registry.owner)

                await add_model_version_resources(applied_migration, db_source, model_version, model.name)

                model.model_versions.append(model_version)
                session.add(model)

                registry.models.append(model)

            await add_objects(applied_migration, db_source, registry, session)
            await delete_objects(applied_migration, db_source, session)
            await alter_objects(applied_migration, db_source, registry, session)

            if object_name:
                object_ = await get_object(source_registry_guid, object_name, session)
                await set_object_synchronized_at(object_)
            else:
                await set_synchronized_at(registry)
                registry.status = Status.ON

            await session.commit()

            await remove_redundant_tags(session)


async def process_graph_migration_failure(graph_migration: dict):
    source_registry_guid = graph_migration['source_registry_guid']

    async with db_session() as session:
        await session.execute(
            update(SourceRegister)
            .where(SourceRegister.guid == source_registry_guid)
            .values(status=Status.ON)
        )


async def add_model_version_resources(
        migration: MigrationOut, db_source: str, model_version: ModelVersion, model_name: str
):
    for schema in migration.schemas:
        for table in schema.tables_to_create:
            resource_db_link = f'{db_source}.{schema.name}.{table.name}'
            resource = ModelResource(
                guid=str(uuid.uuid4()), name=model_name, owner=model_version.owner,
                type='resource', db_link=resource_db_link
            )
            for field in table.fields:
                attr_db_link = f'{resource_db_link}.{field.name}'
                if field.is_key:
                    cardinality = Cardinality.ONE_TO_ONE.value
                else:
                    cardinality = Cardinality.ZERO_TO_ONE.value

                resource_attr = ModelResourceAttribute(
                    guid=str(uuid.uuid4()), name=field.name, key=field.is_key, db_link=attr_db_link,
                    cardinality=cardinality, data_type_id=SYS_DATA_TYPE_TO_ID.get(field.db_type, None),
                    data_type_flag=0
                )
                resource.attributes.append(resource_attr)
            model_version.model_resources.append(resource)


async def get_source_registry(source_registry_guid: str, session: AsyncSession) -> SourceRegister:
    registry = await session.execute(
        select(SourceRegister)
        .options(selectinload(SourceRegister.objects).selectinload(Object.fields))
        .options(selectinload(SourceRegister.models))
        .where(SourceRegister.guid == source_registry_guid)
    )
    registry = registry.scalars().first()
    return registry


async def get_object(source_registry_guid: str, object_name: str, session: AsyncSession):
    object_ = await session.execute(
        select(Object)
        .options(joinedload(Object.source))
        .options(selectinload(Object.fields))
        .where(
            and_(
                Object.source_registry_guid == source_registry_guid,
                Object.name == object_name
            )
        )
    )
    object_ = object_.scalars().first()
    return object_


async def add_objects(
        applied_migration: MigrationOut, db_source: str, source_registry: SourceRegister, session: AsyncSession
):
    objects = await create_objects_from_migration_out(applied_migration, db_source, source_registry.owner, session)
    source_registry.objects.extend(objects)


async def create_objects_from_migration_out(
        migration: MigrationOut, db_source: str, owner: str, session: AsyncSession
) -> list[Object]:
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
            session.add(object_)
            for field in table.fields:
                field_db_path = f'{object_db_path}.{field.name}'
                guid = str(uuid.uuid4())
                field_model = Field(
                    name=field.name, data_type_id=SYS_DATA_TYPE_TO_ID.get(field.db_type, None), guid=guid,
                    is_key=field.is_key, db_path=field_db_path, owner=owner, source_created_at=now,
                    source_updated_at=now, local_updated_at=now, synchronized_at=now, length=len(field.name)
                )
                session.add(field_model)
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
            fields_to_create = await create_fields(
                table.fields_to_create, table_db_path, source_registry.owner, session
            )

            curr_object = object_db_path_to_object[table_db_path]
            curr_object.fields.extend(fields_to_create)

            now = datetime.now()
            curr_object.source_updated_at = now

            fields_to_alter = curr_object.field_db_path_to_field
            for field in table.fields_to_alter:
                field_db_path = f'{table_db_path}.{field.name}'

                field_to_alter_model = fields_to_alter[field_db_path]
                field_to_alter_model.data_type_id = SYS_DATA_TYPE_TO_ID.get(field.new_type, None)
                field_to_alter_model.source_updated_at = now

            for field in table.fields_to_delete:
                field_db_path = f'{table_db_path}.{field}'
                fields_to_delete.append(field_db_path)

    if fields_to_delete:
        await session.execute(
            delete(Field)
            .where(Field.db_path.in_(fields_to_delete))
        )


async def create_fields(
        fields_to_create: list[FieldToCreate], table_db_path: str, owner: str, session: AsyncSession
) -> list[Field]:
    fields = []
    now = datetime.now()
    for field in fields_to_create:
        guid = str(uuid.uuid4())
        field_model = Field(
            name=field.name, data_type_id=SYS_DATA_TYPE_TO_ID.get(field.db_type, None), is_key=field.is_key, guid=guid,
            db_path=f'{table_db_path}.{field.name}', owner=owner, source_created_at=now, source_updated_at=now,
            local_updated_at=now, synchronized_at=now, length=len(field.name)
        )
        session.add(field_model)
        fields.append(field_model)
    return fields


async def set_synchronized_at(source_registry: SourceRegister):
    for object_ in source_registry.objects:
        await set_object_synchronized_at(object_)
    source_registry.synchronized_at = datetime.now()


async def set_object_synchronized_at(object_: Object):
    now = datetime.now()

    object_.synchronized_at = now
    object_.is_synchronized = True

    for field in object_.fields:
        field.synchronized_at = now
