from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import ModelQuality

from sqlalchemy import select


async def read_all(session: AsyncSession):
    model_qualities = await session.execute(
        select(ModelQuality)
    )
    model_qualities = model_qualities.scalars().all()

    return model_qualities


async def read_by_id(id: str, session: AsyncSession):
    model_quality = await session.execute(
        select(ModelQuality)
        .filter(ModelQuality.id == id)
    )

    model_quality = model_quality.scalars().first()

    if not model_quality:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return model_quality