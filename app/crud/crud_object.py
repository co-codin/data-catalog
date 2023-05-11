import asyncio
import uuid
from typing import List

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import load_only, selectinload, joinedload

from app.config import settings
from app.crud.crud_source_registry import add_tags, _get_authors_data_by_guids, _set_author_data, update_tags
from app.models.sources import Object, SourceRegister
from app.schemas.objects import ObjectIn, ObjectManyOut, ObjectOut, ObjectUpdateIn
from app.services.crypto import decrypt
from app.services.metadata_extractor import MetaDataExtractorFactory


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
        .options(joinedload(Object.source))
        .options(selectinload(Object.tags))
        .options(selectinload(Object.comments))
    )
    objects = objects.scalars().all()
    return [ObjectManyOut.from_orm(object_) for object_ in objects]


async def read_by_guid(guid: str, token: str, session: AsyncSession):
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
            None, _get_authors_data_by_guids, author_guids, token
        )
        _set_author_data(object_out.comments, authors_data)

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

    await update_tags(object_model, object_update_in.tags, session)

    session.add(object_model)
    await session.commit()
