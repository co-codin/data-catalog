import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.model import ModelAttitude
from app.schemas.model_attitude import ModelAttitudeIn


async def read_attitudes_by_resource_id(resource_id: int, session: AsyncSession):
    model_attitude = await session.execute(
        select(ModelAttitude)
        .filter(ModelAttitude.resource_id == resource_id)
    )
    model_attitude = model_attitude.scalars().all()
    return model_attitude


async def read_attitude_by_guid(guid: str, token: str, session: AsyncSession):
    model_attitude = await session.execute(
        select(ModelAttitude)
        .filter(ModelAttitude.guid == guid)
    )
    model_attitude = model_attitude.scalars().first()

    if not model_attitude:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return model_attitude


async def create_model_attitude(attitude_in: ModelAttitudeIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())

    model_attitude = ModelAttitude(
        **attitude_in.dict(),
        guid=guid
    )

    session.add(model_attitude)
    await session.commit()

    return model_attitude.guid


async def delete_model_attitude(guid: str, session: AsyncSession):
    await session.execute(
        delete(ModelAttitude)
        .where(ModelAttitude.guid == guid)
    )
    await session.commit()