import uuid

from typing import Iterable

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import load_only

from app.models.sources import Object, Tag, SourceRegister
from app.schemas.objects import ObjectIn
from app.utils.metadata_extractor_utils import get_metadata_extractor_by_conn_string


async def create_object(object_in: ObjectIn, session: AsyncSession):
    guid = str(uuid.uuid4())
    created_at, updated_at = await select_created_at_updated_at_from_source(
        object_in.source_registry_guid, object_in.name, session
    )
    object_model = Object(
        **object_in.dict(exclude={'source_registry_guid', 'tags'}),
        guid=guid,
        source_registry_guid=object_in.source_registry_guid,
        source_created_at=created_at,
        source_updated_at=updated_at
    )
    await add_tags(object_model, object_in.tags, session)
    session.add(object_model)
    await session.commit()
    return guid


async def add_tags(object_model: Object, tags_in: Iterable[str], session: AsyncSession):
    if not tags_in:
        return

    tag_models = await session.execute(
        select(Tag)
        .filter(Tag.name.in_(tags_in))
    )
    tag_models = tag_models.scalars().all()
    tag_models_set = {tag.name for tag in tag_models}

    for tag in tag_models:
        object_model.tags.append(tag)

    for tag in tags_in:
        if tag not in tag_models_set:
            object_model.tags.append(Tag(name=tag))


async def select_created_at_updated_at_from_source(source_registry_guid: str, table_name: str, session: AsyncSession):
    source_registry = await session.execute(
        select(SourceRegister)
        .options(load_only(SourceRegister.conn_string))
        .filter(SourceRegister.guid == source_registry_guid)
    )
    source_registry = source_registry.scalars().first()
    if not source_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    metadata_extractor = await get_metadata_extractor_by_conn_string(source_registry.conn_string)
    created_at, updated_at = await metadata_extractor.extract_created_at_updated_at(table_name=table_name)
    return created_at, updated_at
