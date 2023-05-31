from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import ModelQuality

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.schemas.model_quality import ModelQualityIn, ModelQualityUpdateIn
from app.crud.crud_source_registry import add_tags, update_tags


async def read_all(session: AsyncSession):
    model_qualities = await session.execute(
        select(ModelQuality)
    )
    model_qualities = model_qualities.scalars().all()

    return model_qualities


async def create(model_quality_in: ModelQualityIn, session: AsyncSession):
    model_quality = ModelQuality(
        **model_quality_in.dict(exclude={'tags'}),
    )
    await add_tags(model_quality, model_quality_in.tags, session)

    session.add(model_quality)
    await session.commit()

    return model_quality.guid


async def update_by_id(id: str, model_quality_update_in: ModelQualityUpdateIn, session: AsyncSession):
    model_quality = await session.execute(
        select(ModelQuality)
        .options(selectinload(ModelQuality.tags))
        .filter(ModelQuality.id == id)
    )
    model_quality = model_quality.scalars().first()

    model_quality_update_in_data = {
        key: value for key, value in model_quality_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    await session.execute(
        update(ModelQuality)
        .where(ModelQuality.id == id)
        .values(
            **model_quality_update_in_data,
        )
    )

    await update_tags(model_quality, model_quality_update_in.tags, session)

    session.add(model_quality)
    await session.commit()


async def read_by_id(id: str, session: AsyncSession):
    model_quality = await session.execute(
        select(ModelQuality)
        .filter(ModelQuality.id == id)
    )

    model_quality = model_quality.scalars().first()

    if not model_quality:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return model_quality


async def delete_by_id(id: str, session: AsyncSession):
    await session.execute(
        delete(ModelQuality)
        .where(ModelQuality.id == id)
    )
    await session.commit()