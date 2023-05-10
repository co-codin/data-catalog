import uuid
from typing import List

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload, joinedload

from app.config import settings
from app.crud.crud_source_registry import add_tags
from app.models.sources import Object, SourceRegister
from app.schemas.objects import ObjectIn, ObjectManyOut
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
    )
    objects = objects.scalars().all()
    return [ObjectManyOut.from_orm(object_) for object_ in objects]
