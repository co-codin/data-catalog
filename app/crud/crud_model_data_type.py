from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import ModelDataType

from sqlalchemy import select


async def read_all(session: AsyncSession):
    model_data_types = await session.execute(
        select(ModelDataType)
    )
    model_data_types = model_data_types.scalars().all()

    return model_data_types


async def read_by_id(id: int, session: AsyncSession):
    model_data_type = await session.execute(
        select(ModelDataType)
        .filter(ModelDataType.id == id)
    )

    model_data_type = model_data_type.scalars().first()

    if not model_data_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return model_data_type