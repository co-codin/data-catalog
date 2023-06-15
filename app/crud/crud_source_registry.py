import uuid
import logging
import asyncio

from typing import List, Optional, Set
from datetime import datetime

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_
from sqlalchemy.orm import selectinload, load_only

from app.crud.crud_tag import add_tags, update_tags
from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.models.sources import SourceRegister, Status

from app.schemas.source_registry import (
    SourceRegistryIn, SourceRegistryUpdateIn, SourceRegistryOut, SourceRegistryManyOut, SourceRegistrySynch
)

from app.services.crypto import encrypt, decrypt
from app.services.metadata_extractor import MetaDataExtractorFactory

from app.errors.source_registry_errors import ConnStringAlreadyExist, SourceRegistryNameAlreadyExist
from app.errors.source_registry_errors import SourceRegistryIsNotOnError

from app.config import settings

logger = logging.getLogger(__name__)


async def create_source_registry(source_registry_in: SourceRegistryIn, session: AsyncSession) -> SourceRegister:
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
    return source_registry_model


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


async def edit_source_registry(guid: str, source_registry_update_in: SourceRegistryUpdateIn, session: AsyncSession):
    driver = source_registry_update_in.conn_string.split('://', maxsplit=1)[0]
    encrypted_conn_string = encrypt(settings.encryption_key, source_registry_update_in.conn_string)
    await session.execute(
        update(SourceRegister)
        .where(SourceRegister.guid == guid)
        .values(
            **source_registry_update_in.dict(exclude={'tags', 'conn_string'}),
            type=driver,
            conn_string=encrypted_conn_string,
            updated_at=datetime.utcnow()
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

    await update_tags(source_registry_model, session, source_registry_update_in.tags)

    session.add(source_registry_model)
    await session.commit()


async def set_source_registry_status(guid: str, status_in: Status, session: AsyncSession):
    await session.execute(
        update(SourceRegister)
        .where(SourceRegister.guid == guid)
        .values(status=status_in)
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
            None, get_authors_data_by_guids, author_guids, token
        )
        set_author_data(source_registry_out.comments, authors_data)

    return source_registry_out


async def read_source_registry_by_guid(guid: str, session: AsyncSession) -> SourceRegistrySynch:
    source_registry = await session.execute(
        select(SourceRegister)
        .where(SourceRegister.guid == guid)
    )

    source_registry = source_registry.scalars().first()
    if not source_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    elif source_registry.status != Status.ON:
        raise SourceRegistryIsNotOnError(source_registry.status)

    source_registry.status = Status.SYNCHRONIZING
    session.add(source_registry)

    decrypted_conn_string = decrypt(settings.encryption_key, source_registry.conn_string)
    source_registry_synch = SourceRegistrySynch(
        source_registry_guid=source_registry.guid, conn_string=decrypted_conn_string
    )
    return source_registry_synch


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
