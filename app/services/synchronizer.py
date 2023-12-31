import json
import uuid
import logging

from datetime import datetime
from enum import Enum
from json2xml import json2xml

from sqlalchemy import select, delete, update, and_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession


from app.crud.crud_tag import remove_redundant_tags, add_tags
from app.enums.enums import Cardinality, SyncType
from app.models import (
    SourceRegister, Object, Field, Status, Model, ModelVersion, ModelResource, ModelResourceAttribute, LogType
)
from app.mq import create_channel
from app.schemas.log import LogIn
from app.schemas.migration import MigrationOut, FieldToCreate, MigrationPattern
from app.schemas.model import ModelCommon
from app.database.sqlalchemy import db_session
from app.constants.data_types import SYS_DATA_TYPE_TO_ID, ID_TO_SYS_DATA_TYPE
from app.config import settings
from app.services.log import add_log
from app.models.log import LogEvent, LogName, LogText

logger = logging.getLogger(__name__)


class MigrationRequestStatus(Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'


async def send_for_synchronization(
        source_guid: str, conn_string: str, migration_pattern: MigrationPattern, identity_id: str,
        sync_type: int, model_in: ModelCommon | None = None, object_name: str | None = None,
        object_guid: str | None = None, object_db_path: str | None = None, source_name: str | None = None
):
    db_source = conn_string.rsplit('/', maxsplit=1)[1]

    if object_name:
        migration_name = f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}.{db_source}.{object_name}'
    else:
        migration_name = f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}.{db_source}'

    params = {
        'name': migration_name,
        'conn_string': conn_string,
        'migration_pattern': migration_pattern.dict(),
        'source_guid': source_guid,
        'object_name': object_name,
        'source_name': source_name,
        'model': model_in.dict() if model_in else None,
        'object_guid': object_guid,
        'object_db_path': object_db_path,
        'identity_id': identity_id,
        'sync_type': sync_type
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
    logger.info("Processing graph migration success...")
    if graph_migration:
        applied_migration = MigrationOut(**graph_migration['graph_migration'])
        source_guid = graph_migration['source_guid']
        source_name = graph_migration['source_name']
        conn_string = graph_migration['conn_string']
        object_name = graph_migration['object_name']
        object_guid = graph_migration['object_guid']
        model_in = graph_migration['model']
        count = graph_migration['count']

        async with db_session() as session:
            registry = await get_source_registry(source_guid, session)
            db_source = conn_string.rsplit('/', maxsplit=1)[1]

            if model_in:
                model = Model(
                    name=model_in['name'], short_desc=model_in['short_desc'], business_desc=model_in['business_desc'],
                    guid=str(uuid.uuid4()), owner=registry.owner
                )
                await add_tags(model, model_in['tags'], session)
                model_version = ModelVersion(guid=str(uuid.uuid4()), owner=registry.owner)

                await add_model_version_resources(applied_migration, db_source, model_version)

                model.model_versions.append(model_version)
                session.add(model)

                registry.models.append(model)

            await delete_objects(applied_migration, db_source, session)
            await alter_objects(applied_migration, db_source, registry, session)

            if not object_name:
                # synchronizing source
                await add_objects(applied_migration, db_source, registry, session)
                await set_synchronized_at(registry)
                registry.status = Status.ON
            else:
                # synchronizing object
                object_ = await get_object(source_guid, object_name, session)
                if object_:
                    if len(applied_migration.schemas) == 1 and len(applied_migration.schemas[0].tables_to_create) == 1:
                        # adding fields for already existing object
                        schema = applied_migration.schemas[0]
                        table = applied_migration.schemas[0].tables_to_create[0]
                        db_path = f'{db_source}.{schema.name}.{table.name}'

                        object_.db_path = db_path
                        fields = await create_fields(table.fields, db_path, object_.owner, session)
                        object_.fields.extend(fields)

                        if not object_.source_created_at:
                            object_.source_created_at = datetime.utcnow()
                        if not object_.source_updated_at:
                            object_.source_updated_at = datetime.utcnow()

                    await set_object_synchronized_at(object_)

            await log_graph_migration_success(
                applied_migration=applied_migration,
                synch_type=graph_migration['sync_type'],
                source_name=source_name,
                source_guid=source_guid,
                object_name=object_name,
                object_guid=object_guid,
                identity_id=graph_migration['identity_id'],
                count=count,
                session=session
            )
        await session.commit()
        await remove_redundant_tags()


async def log_graph_migration_success(
        applied_migration: MigrationOut, synch_type: str, source_name: str, source_guid: str,
        object_name: str, object_guid: str, identity_id: str, count: int, session: AsyncSession
):
    added_objects_len, altered_objects_len, deleted_objects_len = count_objects(applied_migration)
    match synch_type:
        case SyncType.ADD_SOURCE.value:
            await add_log(session, LogIn(
                type=LogType.SOURCE_REGISTRY.value,
                log_name=LogName.SOURCE_ADD.value,
                text=LogText.SYNC_SUCCESS.value.format(
                    name=source_name,
                    added=added_objects_len,
                    altered=altered_objects_len,
                    deleted=deleted_objects_len,
                    not_changed=count - added_objects_len - altered_objects_len - deleted_objects_len
                ),
                identity_id=identity_id,
                event=LogEvent.SYNC_SOURCE_AUTO.value,
                properties=json.dumps({'source_guid': source_guid})
            ))
        case SyncType.SYNC_SOURCE.value:
            await add_log(session, LogIn(
                type=LogType.SOURCE_REGISTRY.value,
                log_name=LogName.SOURCE_SYNC.value,
                text=LogText.SYNC_SUCCESS.value.format(
                    name=source_name,
                    added=added_objects_len,
                    altered=altered_objects_len,
                    deleted=deleted_objects_len,
                    not_changed=count - added_objects_len - altered_objects_len - deleted_objects_len
                ),
                identity_id=identity_id,
                event=LogEvent.SYNC_SOURCE_MANUAL.value,
                properties=json.dumps({'source_guid': source_guid})
            ))
        case SyncType.ADD_OBJECT.value:
            await add_log(session, LogIn(
                type=LogType.DATA_CATALOG.value,
                log_name=LogName.OBJECT_ADD.value,
                text=LogText.SYNC_SUCCESS.value.format(
                    name=object_name,
                    added=added_objects_len,
                    altered=altered_objects_len,
                    deleted=deleted_objects_len,
                    not_changed=count - 1
                ),
                identity_id=identity_id,
                event=LogEvent.SYNC_OBJECT.value,
                not_changed=count - 1,
                properties=json.dumps({'object_guid': object_guid})
            ))
        case SyncType.SYNC_OBJECT.value:
            await add_log(session, LogIn(
                type=LogType.DATA_CATALOG.value,
                log_name=LogName.OBJECT_SYNC.value,
                text=LogText.SYNC_SUCCESS.value.format(
                    name=object_name,
                    added=added_objects_len,
                    altered=altered_objects_len,
                    deleted=deleted_objects_len,
                    not_changed=count - 1
                ),
                identity_id=identity_id,
                event=LogEvent.SYNC_OBJECT.value,
                properties=json.dumps({'object_guid': object_guid})
            ))


async def log_graph_migration_failure(
        sync_type: str, source_name: str, source_guid: str,
        object_name: str, object_guid: str, identity_id: str, session: AsyncSession
):
    match sync_type:
        case SyncType.SYNC_OBJECT.value:
            await add_log(session, LogIn(
                type=LogType.DATA_CATALOG.value,
                log_name=LogName.OBJECT_SYNC.value,
                text=LogText.SYNC_ERROR.value.format(name=object_name),
                identity_id=identity_id,
                event=LogEvent.SYNC_OBJECT.value,
                properties=json.dumps({'object_guid': object_guid})
            ))
        case SyncType.ADD_OBJECT.value:
            await add_log(session, LogIn(
                type=LogType.DATA_CATALOG.value,
                log_name=LogName.OBJECT_ADD.value,
                text=LogText.SYNC_ERROR.value.format(name=object_name),
                identity_id=identity_id,
                event=LogEvent.ADD_OBJECT.value,
            ))
        case SyncType.SYNC_SOURCE.value:
            await add_log(session, LogIn(
                type=LogType.SOURCE_REGISTRY.value,
                log_name=LogName.SOURCE_SYNC.value,
                text=LogText.SYNC_ERROR.value.format(name=source_name),
                identity_id=identity_id,
                event=LogEvent.SYNC_SOURCE_MANUAL.value,
                properties=json.dumps({'source_guid': source_guid})
            ))
        case SyncType.ADD_SOURCE.value:
            await add_log(session, LogIn(
                type=LogType.SOURCE_REGISTRY.value,
                log_name=LogName.SOURCE_ADD.value,
                text=LogText.SYNC_ERROR.value.format(name=source_name),
                identity_id=identity_id,
                event=LogEvent.SYNC_SOURCE_AUTO.value,
                properties=json.dumps({'source_guid': source_guid})
            ))


def count_objects(applied_migration: MigrationOut) -> (int, int, int):
    added_objects_len, altered_objects_len, deleted_objects_len = 0, 0, 0
    for schema in applied_migration.schemas:
        added_objects_len += len(schema.tables_to_create)
        altered_objects_len += len(schema.tables_to_alter)
        deleted_objects_len += len(schema.tables_to_delete)
    return added_objects_len, altered_objects_len, deleted_objects_len


async def process_graph_migration_failure(graph_migration: dict):
    logger.info("Processing graph migration failure...")
    logger.info(f"Received failure msg: {graph_migration}")

    source_guid = graph_migration['source_guid']
    object_guid = graph_migration['object_guid']

    async with db_session() as session:
        await session.execute(
            update(SourceRegister)
            .where(SourceRegister.guid == source_guid)
            .values(status=Status.ON)
        )
        if object_guid:
            await session.execute(
                update(Object)
                .where(Object.guid == object_guid)
                .values(is_synchronizing=False)
            )

        await log_graph_migration_failure(
            sync_type=graph_migration['sync_type'],
            source_name=graph_migration['source_name'], source_guid=source_guid,
            object_name=graph_migration['object_name'], object_guid=object_guid,
            identity_id=graph_migration['identity_id'], session=session
        )


async def add_model_version_resources(migration: MigrationOut, db_source: str, model_version: ModelVersion):
    for schema in migration.schemas:
        for table in schema.tables_to_create:
            resource_db_link = f'{db_source}.{schema.name}.{table.name}'
            resource_type = 'Ресурс'

            resource = ModelResource(
                guid=str(uuid.uuid4()), name=table.name, owner=model_version.owner,
                type=resource_type, db_link=resource_db_link
            )
            model_resource_json = {
                'name': resource.name, 'type': resource_type, 'desc': '', 'db_link': resource_db_link, 'tags': [],
                'attrs': []
            }

            for field in table.fields:
                attr_db_link = f'{resource_db_link}.{field.name}'
                if field.is_key:
                    cardinality = Cardinality.ONE_TO_ONE.value
                else:
                    cardinality = Cardinality.ZERO_TO_ONE.value

                resource_attr = ModelResourceAttribute(
                    guid=str(uuid.uuid4()), name=field.name, key=field.is_key, db_link=attr_db_link,
                    cardinality=cardinality, model_data_type_id=SYS_DATA_TYPE_TO_ID.get(field.db_type, None)
                )
                model_resource_attr = {
                    'name': resource_attr.name, 'is_key': resource_attr.key,
                    'data_type': ID_TO_SYS_DATA_TYPE.get(resource_attr.model_data_type_id, None),
                    'db_link': resource_attr.db_link, 'cardinality': resource_attr.cardinality, 'desc': '',
                    'tags': []
                }
                model_resource_json['attrs'].append(model_resource_attr)
                resource.attributes.append(resource_attr)
            model_resource_xml = json2xml.Json2xml(model_resource_json, wrapper='all', pretty=True).to_xml()

            resource.json = model_resource_json
            resource.xml = model_resource_xml
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
        applied_migration: MigrationOut, db_source: str, source: SourceRegister, session: AsyncSession
):
    objects = await create_objects_from_migration_out(applied_migration, db_source, source, session)
    source.objects.extend(objects)


async def create_objects_from_migration_out(
        migration: MigrationOut, db_source: str, source: SourceRegister, session: AsyncSession
) -> list[Object]:
    tables = []
    for schema in migration.schemas:
        for table in schema.tables_to_create:
            object_db_path = f'{db_source}.{schema.name}.{table.name}'
            now = datetime.utcnow()
            guid = str(uuid.uuid4())
            object_ = Object(
                name=table.name, owner=source.owner, db_path=object_db_path, source_created_at=now, guid=guid,
                source_updated_at=now, local_updated_at=now, synchronized_at=now, is_synchronizing=False
            )
            session.add(object_)

            fields = await create_fields(table.fields, object_db_path, source.owner, session)
            object_.fields.extend(fields)
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
        applied_migration: MigrationOut, db_source: str, source: SourceRegister, session: AsyncSession
):
    tables_to_alter = {
        f'{db_source}.{schema.name}.{table.name}'
        for schema in applied_migration.schemas
        for table in schema.tables_to_alter
    }
    if not tables_to_alter:
        return

    object_db_path_to_object: dict[str: Object] = source.object_db_path_to_object(tables_to_alter)
    fields_to_delete = []

    for schema in applied_migration.schemas:
        for table in schema.tables_to_alter:
            table_db_path = f'{db_source}.{schema.name}.{table.name}'
            fields_to_create = await create_fields(
                table.fields_to_create, table_db_path, source.owner, session
            )

            curr_object = object_db_path_to_object[table_db_path]
            curr_object.fields.extend(fields_to_create)

            now = datetime.utcnow()
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
    now = datetime.utcnow()
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
    source_registry.synchronized_at = datetime.utcnow()


async def set_object_synchronized_at(object_: Object):
    now = datetime.utcnow()

    object_.synchronized_at = now
    object_.is_synchronizing = False

    for field in object_.fields:
        field.synchronized_at = now
