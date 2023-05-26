import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.crud_source_registry import add_tags, update_tags
from sqlalchemy import select, update, delete

from app.models.model import ModelVersion
from app.schemas.model_version import ModelVersionIn, ModelVersionUpdateIn

from sqlalchemy.orm import selectinload
from datetime import datetime


async def create_model_version(model_version_in: ModelVersionIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())
    
    model_version = ModelVersion(
        **model_version_in.dict(exclude={'tags'}),
        guid=guid
    )
    await add_tags(model_version, model_version_in.tags, session)

    session.add(model_version)
    await session.commit()

    return model_version.guid

async def update_model_version(guid: str, model_version_update_in: ModelVersionUpdateIn, session: AsyncSession):
    model_version_update_in_data = {
        key: value for key, value in model_version_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    await session.execute(
        update(ModelVersion)
        .where(ModelVersion.guid == guid)
        .values(
            **model_version_update_in_data,
        )
    )

    model_version = await session.execute(
        select(ModelVersion)
        .options(selectinload(ModelVersion.tags))
        .filter(ModelVersion.guid == guid)
    )
    model_version = model_version.scalars().first()
    if not model_version:
        return

    await update_tags(model_version, model_version_update_in.tags, session)

    session.add(model_version)
    await session.commit()


async def read_by_guid(guid: str, session: AsyncSession):
    model_version = await session.execute(
        select(ModelVersion)
        .options(selectinload(ModelVersion.tags))
        .filter(ModelVersion.guid == guid)
    )

    model_version = model_version.scalars().first()

    if not model_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


    return model_version


async def delete_model_version(guid: str, session: AsyncSession):
    await session.execute(
        delete(ModelVersion)
        .where(ModelVersion.guid == guid)
    )
    await session.commit()