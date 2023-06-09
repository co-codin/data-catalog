import uuid
import asyncio

from fastapi import HTTPException, status

from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ModelQuality

from app.schemas.model_quality import ModelQualityIn, ModelQualityUpdateIn, ModelQualityOut
from app.crud.crud_source_registry import add_tags, update_tags
from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.errors.model_quality import ModelQualityNameAlreadyExist


async def read_all(model_version_id: str, session: AsyncSession):
    model_qualities = await session.execute(
        select(ModelQuality)
        .filter(ModelQuality.model_version_id == model_version_id)
        .options(selectinload(ModelQuality.comments))
    )
    model_qualities = model_qualities.scalars().all()

    return model_qualities


async def create(model_quality_in: ModelQualityIn, session: AsyncSession):
    guid = str(uuid.uuid4())

    model_quality = ModelQuality(
        **model_quality_in.dict(exclude={'tags'}),
        guid=guid
    )
    await add_tags(model_quality, model_quality_in.tags, session)

    session.add(model_quality)
    await session.commit()

    return model_quality.guid


async def check_on_model_quality_uniqueness(
        name: str, session: AsyncSession, model_version_id: int = None, guid: str = None
):
    if not model_version_id:
        model_quality = await session.execute(
            select(ModelQuality)
            .where(ModelQuality.guid == guid)
        )
        model_quality = model_quality.scalars().first()
        model_version_id = model_quality.model_version_id

    model_qualities = await session.execute(
        select(ModelQuality)
        .where(
            and_(
                ModelQuality.model_version_id == model_version_id,
                ModelQuality.name == name
            )
        )
    )
    model_qualities = model_qualities.scalars().all()

    for model_quality in model_qualities:
        if model_quality.name == name and model_quality.guid != guid:
            raise ModelQualityNameAlreadyExist(name)


async def update_by_guid(guid: str, model_quality_update_in: ModelQualityUpdateIn, session: AsyncSession):
    model_quality = await session.execute(
        select(ModelQuality)
        .options(selectinload(ModelQuality.tags))
        .filter(ModelQuality.guid == guid)
    )
    model_quality = model_quality.scalars().first()

    model_quality_update_in_data = {
        key: value for key, value in model_quality_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    await session.execute(
        update(ModelQuality)
        .where(ModelQuality.guid == guid)
        .values(
            **model_quality_update_in_data,
        )
    )

    await update_tags(model_quality, session, model_quality_update_in.tags)

    session.add(model_quality)
    await session.commit()


async def read_by_guid(guid: str, token: str, session: AsyncSession) -> ModelQualityOut:
    model_quality = await session.execute(
        select(ModelQuality)
        .options(selectinload(ModelQuality.comments))
        .where(ModelQuality.guid == guid)
    )

    model_quality = model_quality.scalars().first()

    if not model_quality:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    model_quality_out = ModelQualityOut.from_orm(model_quality)

    if model_quality.comments:
        author_guids = {comment.author_guid for comment in model_quality.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, get_authors_data_by_guids, author_guids, token
        )
        set_author_data(model_quality_out.comments, authors_data)

    return model_quality_out


async def delete_by_guid(guid: str, session: AsyncSession):
    await session.execute(
        delete(ModelQuality)
        .where(ModelQuality.guid == guid)
    )
    await session.commit()
