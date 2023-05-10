import uuid
import logging
import requests
import asyncio

from typing import List, Dict, Iterable, Optional, Set, Union

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, and_
from sqlalchemy.orm import selectinload, joinedload, load_only

from app.schemas.source_registry import (
    SourceRegistryIn, SourceRegistryUpdateIn, SourceRegistryOut, CommentOut, SourceRegistryManyOut
)
from app.models.sources import SourceRegister, Tag, Status, Object
from app.services.crypto import encrypt, decrypt
from app.services.metadata_extractor import MetaDataExtractorFactory
from app.errors import ConnStringAlreadyExist, SourceRegistryNameAlreadyExist
from app.config import settings

logger = logging.getLogger(__name__)


async def create_source_registry(source_registry_in: SourceRegistryIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())
    driver = source_registry_in.conn_string.split('://', maxsplit=1)[0]
    encrypted_conn_string = encrypt(settings.encryption_key, source_registry_in.conn_string)
    source_registry_model = SourceRegister(
        **source_registry_in.dict(exclude={'tags', 'conn_string'}),
        guid=guid,
        type=driver,
        conn_string=encrypted_conn_string
    )
    await add_tags(source_registry_model, source_registry_in.tags, session)

    session.add(source_registry_model)
    await session.commit()

    return source_registry_model.guid


async def check_on_uniqueness(name: str, conn_string: str, session: AsyncSession, guid: Optional[str] = None):
    source_registries = await session.execute(
        select(SourceRegister)
        .options(load_only(SourceRegister.conn_string, SourceRegister.name, SourceRegister.guid))
        .filter(
            or_(
                SourceRegister.conn_string.is_not(None),
                SourceRegister.name == name
            )
        )
    )
    source_registries = source_registries.scalars().all()
    for source_registry in source_registries:
        if source_registry.name == name and source_registry.guid != guid:
            raise SourceRegistryNameAlreadyExist(name)
        else:
            decrypted_conn_string = decrypt(settings.encryption_key, source_registry.conn_string)
            if conn_string == decrypted_conn_string and source_registry.guid != guid:
                raise ConnStringAlreadyExist(conn_string)


async def add_tags(tags_like_model: Union[SourceRegister, Object], tags_in: Iterable[str], session: AsyncSession):
    if not tags_in:
        return

    tag_models = await session.execute(
        select(Tag)
        .filter(Tag.name.in_(tags_in))
    )
    tag_models = tag_models.scalars().all()
    tag_models_set = {tag.name for tag in tag_models}

    tags_like_model.tags.extend(tag_models)
    tags_like_model.tags.extend(
        (Tag(name=tag) for tag in tags_in if tag not in tag_models_set)
    )


async def edit_source_registry(guid: str, source_registry_update_in: SourceRegistryUpdateIn, session: AsyncSession):
    driver = source_registry_update_in.conn_string.split('://', maxsplit=1)[0]
    encrypted_conn_string = encrypt(settings.encryption_key, source_registry_update_in.conn_string)
    await session.execute(
        update(SourceRegister)
        .where(SourceRegister.guid == guid)
        .values(
            **source_registry_update_in.dict(exclude={'tags', 'conn_string'}),
            type=driver,
            conn_string=encrypted_conn_string
        )
    )

    source_registry_model = await session.execute(
        select(SourceRegister)
        .options(selectinload(SourceRegister.tags))
        .filter(SourceRegister.guid == guid)
    )
    source_registry_model = source_registry_model.scalars().first()
    if not source_registry_model:
        return

    await update_tags(source_registry_model, source_registry_update_in.tags, session)

    session.add(source_registry_model)
    await session.commit()


async def update_tags(tags_like_model: Union[SourceRegister, Object], tags_update_in: List[str], session: AsyncSession):
    tags_update_in_set = {tag for tag in tags_update_in}
    tags_model_set = {tag.name for tag in tags_like_model.tags}
    tags_model_dict = {tag.name: tag for tag in tags_like_model.tags}

    tags_to_delete = tags_model_set - tags_update_in_set
    for tag in tags_to_delete:
        tags_like_model.tags.remove(tags_model_dict[tag])

    tags_to_create = tags_update_in_set - tags_model_set
    await add_tags(tags_like_model, tags_to_create, session)


async def set_source_registry_status(guid: str, status_in: Status, session: AsyncSession):
    await session.execute(
        update(SourceRegister)
        .where(SourceRegister.guid == guid)
        .values(status=status_in)
    )
    await session.commit()


async def remove_redundant_tags(session: AsyncSession):
    tags = await session.execute(
        select(Tag)
        .options(load_only(Tag.id), joinedload(Tag.source_registries), joinedload(Tag.objects))
        .where(
            and_(
                ~Tag.source_registries.any(),
                ~Tag.objects.any()
            )
        )
    )

    tags = tags.scalars().unique()
    if not tags:
        return

    tag_ids = [tag.id for tag in tags]
    await session.execute(
        delete(Tag)
        .where(Tag.id.in_(tag_ids))
    )
    await session.commit()


async def read_all(session: AsyncSession) -> List[SourceRegistryManyOut]:
    source_registries = await session.execute(
        select(SourceRegister)
        .options(selectinload(SourceRegister.tags))
        .options(selectinload(SourceRegister.comments))
        .order_by(SourceRegister.created_at)
    )
    source_registries = source_registries.scalars().all()
    if not source_registries:
        return source_registries

    source_registries_out = [SourceRegistryManyOut.from_orm(source_registry) for source_registry in source_registries]
    return source_registries_out


async def read_by_guid(guid: str, token: str, session: AsyncSession) -> SourceRegistryOut:
    source_registry = await session.execute(
        select(SourceRegister)
        .options(selectinload(SourceRegister.tags))
        .options(selectinload(SourceRegister.comments))
        .filter(SourceRegister.guid == guid)
    )

    source_registry = source_registry.scalars().first()
    if not source_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    decrypted_conn_string = decrypt(settings.encryption_key, source_registry.conn_string)
    source_registry_out = SourceRegistryOut.from_orm(source_registry)
    source_registry_out.conn_string = decrypted_conn_string

    if source_registry_out.comments:
        author_guids = {comment.author_guid for comment in source_registry.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, _get_authors_data_by_guids, author_guids, token
        )
        _set_author_data(source_registry_out.comments, authors_data)

    return source_registry_out


def _get_authors_data_by_guids(guids: Iterable[str], token: str) -> Dict[str, Dict[str, str]]:
    response = requests.get(
        f'{settings.api_iam}/internal/users/',
        json={'guids': tuple(guids)},
        headers={"Authorization": f"Bearer {token}"}
    )
    authors_data = response.json()
    return authors_data


def _set_author_data(comments: Iterable[CommentOut], authors_data: Dict[str, Dict[str, str]]):
    for comment in comments:
        comment.author_first_name = authors_data[comment.author_guid]['first_name']
        comment.author_last_name = authors_data[comment.author_guid]['last_name']
        comment.author_middle_name = authors_data[comment.author_guid]['middle_name']
        comment.author_email = authors_data[comment.author_guid]['email']


async def read_names_by_status(status_in: Status, session: AsyncSession):
    source_registries = await session.execute(
        select(SourceRegister)
        .options(load_only(SourceRegister.guid, SourceRegister.name))
        .filter(SourceRegister.status == status_in)
    )
    source_registries = source_registries.scalars().all()
    return {
        source_registry.name: source_registry.guid
        for source_registry in source_registries
    }


async def get_objects(guid: str, session: AsyncSession) -> Set[str]:
    source_registry = await session.execute(
        select(SourceRegister)
        .options(selectinload(SourceRegister.objects))
        .filter(SourceRegister.guid == guid)
    )
    source_registry = source_registry.scalars().first()
    if not source_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    decrypted_conn_string = decrypt(settings.encryption_key, source_registry.conn_string)
    metadata_extractor = MetaDataExtractorFactory.build(decrypted_conn_string)
    source_table_names = await metadata_extractor.extract_table_names()
    local_table_names = {
        object_.name
        for object_ in source_registry.objects
    }
    return source_table_names - local_table_names
