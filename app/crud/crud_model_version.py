import asyncio
import uuid

from datetime import datetime

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload

from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.crud.crud_tag import add_tags, update_tags
from app.models.models import ModelVersion
from app.schemas.model_version import ModelVersionIn, ModelVersionUpdateIn


async def read_all(model_id: str, session: AsyncSession):
    model_versions = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.model_id == model_id)
        .options(selectinload(ModelVersion.comments))
    )
    model_versions = model_versions.scalars().all()
    return model_versions


async def create_model_version(model_version_in: ModelVersionIn, session: AsyncSession) -> ModelVersion:
    guid = str(uuid.uuid4())
    
    model_version = ModelVersion(
        **model_version_in.dict(exclude={'tags'}),
        guid=guid
    )
    await add_tags(model_version, model_version_in.tags, session)

    session.add(model_version)
    return model_version


async def update_model_version(guid: str, model_version_update_in: ModelVersionUpdateIn, session: AsyncSession):
    model_version = await session.execute(
        select(ModelVersion)
        .options(selectinload(ModelVersion.tags))
        .filter(ModelVersion.guid == guid)
    )
    model_version = model_version.scalars().first()

    approved_model_version = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.model_id == model_version.model_id)
        .filter(ModelVersion.status == 'approved')
        .order_by(ModelVersion.id)
    )
    approved_model_version = approved_model_version.scalars().first()

    if not model_version.status == 'draft':
        model_version_update_in.status = model_version.status
    elif model_version.status == 'draft' and approved_model_version and model_version_update_in.status == 'approved':
        approved_model_version.status = 'archive'
        model_version.confirmed_at = datetime.now()

    model_version_update_in_data = {
        key: value for key, value in model_version_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    if model_version.status == 'draft' and not model_version.version:
        model_version_update_in_data['version'] = str(uuid.uuid4())

    await session.execute(
        update(ModelVersion)
        .where(ModelVersion.guid == guid)
        .values(
            **model_version_update_in_data,
        )
    )

    await update_tags(model_version, session, model_version_update_in.tags)

    session.add(model_version)
    await session.commit()


async def read_by_guid(guid: str, token: str, session: AsyncSession):
    model_version = await session.execute(
        select(ModelVersion)
        .options(selectinload(ModelVersion.tags))
        .options(selectinload(ModelVersion.comments))
        .options(joinedload(ModelVersion.model_qualities))
        .filter(ModelVersion.guid == guid)
    )

    model_version = model_version.scalars().first()

    if not model_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if model_version.comments:
        author_guids = {comment.author_guid for comment in model_version.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, get_authors_data_by_guids, author_guids, token
        )
        set_author_data(model_version.comments, authors_data)

    return model_version


async def delete_model_version(guid: str, session: AsyncSession):
    model_version = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.guid == guid)
    )
    model_version = model_version.scalars().first()

    if not model_version.status == 'draft':
        raise HTTPException(status_code=403, detail='Можно удалить только черновика')

    await session.execute(
        delete(ModelVersion)
        .where(ModelVersion.guid == guid)
    )
    await session.commit()
