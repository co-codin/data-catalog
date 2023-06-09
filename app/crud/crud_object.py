import asyncio
import uuid
from typing import List

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import load_only, selectinload, joinedload

from app.config import settings
from app.constants.data_types import SYS_DATA_TYPE_TO_ID, ID_TO_SYS_DATA_TYPE
from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.crud.crud_tag import add_tags, update_tags
from app.models.sources import Object, SourceRegister, Field, Status
from app.models.models import ModelDataType
from app.schemas.comment import CommentIn
from app.schemas.objects import ObjectIn, ObjectManyOut, ObjectOut, ObjectUpdateIn, FieldManyOut, ObjectSynch
from app.schemas.tag import TagOut
from app.services.crypto import decrypt
from app.services.metadata_extractor import MetaDataExtractorFactory
from app.errors.source_registry_errors import SourceRegistryIsNotOnError


async def create_object(object_in: ObjectIn, session: AsyncSession):
    guid = str(uuid.uuid4())
    created_at, updated_at = await select_created_at_updated_at_from_source(
        object_in.source_registry_guid, object_in.name, session
    )
    object_model = Object(
        **object_in.dict(exclude={'tags'}),
        guid=guid,
        source_created_at=created_at,
        source_updated_at=updated_at
    )
    await add_tags(object_model, object_in.tags, session)
    session.add(object_model)
    await session.commit()
    return guid


async def select_created_at_updated_at_from_source(source_registry_guid: str, table_name: str, session: AsyncSession):
    source_registry = await session.execute(
        select(SourceRegister)
        .options(load_only(SourceRegister.conn_string))
        .filter(SourceRegister.guid == source_registry_guid)
    )
    source_registry = source_registry.scalars().first()
    if not source_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    decrypted_conn_string = decrypt(settings.encryption_key, source_registry.conn_string)
    metadata_extractor = MetaDataExtractorFactory.build(decrypted_conn_string)
    created_at, updated_at = await metadata_extractor.extract_created_at_updated_at(table_name=table_name)
    return created_at, updated_at


async def read_all(session: AsyncSession) -> List[ObjectManyOut]:
    objects = await session.execute(
        select(Object)
        .options(joinedload(Object.source, innerjoin=True))
        .options(selectinload(Object.tags))
        .options(selectinload(Object.comments))
    )
    objects = objects.scalars().all()
    return [ObjectManyOut.from_orm(object_) for object_ in objects]


async def read_by_guid(guid: str, token: str, session: AsyncSession) -> ObjectOut:
    object_ = await session.execute(
        select(Object)
        .options(selectinload(Object.source), selectinload(Object.tags), selectinload(Object.comments))
        .where(Object.guid == guid)
    )
    object_ = object_.scalars().first()
    if not object_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    object_out = ObjectOut.from_orm(object_)

    if object_out.comments:
        author_guids = {comment.author_guid for comment in object_out.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, get_authors_data_by_guids, author_guids, token
        )
        set_author_data(object_out.comments, authors_data)

    return object_out


async def edit_object(guid: str, object_update_in: ObjectUpdateIn, session: AsyncSession):
    await session.execute(
        update(Object)
        .where(Object.guid == guid)
        .values(
            **object_update_in.dict(exclude={'tags'}),
        )
    )

    object_model = await session.execute(
        select(Object)
        .options(selectinload(Object.tags))
        .filter(Object.guid == guid)
    )
    object_model = object_model.scalars().first()
    if not object_model:
        return

    await update_tags(object_model, session, object_update_in.tags)

    session.add(object_model)
    await session.commit()


async def edit_is_synchronized(guid: str, is_synchronized: bool, session: AsyncSession):
    await session.execute(
        update(Object)
        .where(Object.guid == guid)
        .values(is_synchronized=is_synchronized)
    )
    await session.commit()


async def select_object_fields(guid: str, session: AsyncSession) -> list[FieldManyOut]:
    fields = await session.execute(
        select(Field)
        .options(selectinload(Field.tags), selectinload(Field.comments))
        .where(Field.object_guid == guid)
    )
    fields = fields.scalars().all()

    return [
        FieldManyOut(
            guid=field.guid, is_key=field.is_key, name=field.name,
            type=ID_TO_SYS_DATA_TYPE.get(field.data_type_id, None), length=len(field.name), owner=field.owner,
            desc=field.desc, local_updated_at=field.local_updated_at, synchronized_at=field.synchronized_at,
            source_updated_at=field.source_updated_at,
            tags=[TagOut.from_orm(tag) for tag in field.tags],
            comments=[CommentIn.from_orm(comment) for comment in field.comments]
        )
        for field in fields
    ]


async def read_object_by_guid(guid: str, session: AsyncSession) -> ObjectSynch:
    object_ = await session.execute(
        select(Object)
        .options(joinedload(Object.source, innerjoin=True))
        .where(Object.guid == guid)
    )
    object_ = object_.scalars().first()
    if not object_:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    elif object_.source.status != Status.ON:
        raise SourceRegistryIsNotOnError(object_.source.status)

    object_.is_synchronized = False

    decrypted_conn_string = decrypt(settings.encryption_key, object_.source.conn_string)
    object_sync = ObjectSynch(
        object_name=object_.name, conn_string=decrypted_conn_string, source_registry_guid=object_.source.guid
    )
    return object_sync
