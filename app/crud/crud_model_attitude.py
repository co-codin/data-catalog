import uuid

from sqlalchemy import select, delete, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.crud_model_version import generate_version_number, VersionLevel
from app.errors.errors import ModelAttitudeAttributesError
from app.models.models import ModelAttitude, ModelResourceAttribute, ModelResource
from app.schemas.model_attitude import ModelAttitudeIn


async def read_attitudes_by_resource_id(resource_id: int, session: AsyncSession):
    model_attitude = await session.execute(
        select(ModelAttitude)
        .options(selectinload(ModelAttitude.left_attributes).selectinload(ModelResourceAttribute.resources))
        .options(selectinload(ModelAttitude.right_attributes).selectinload(ModelResourceAttribute.resources))
        .filter(ModelAttitude.resource_id == resource_id)
    )
    model_attitude = model_attitude.scalars().all()
    return model_attitude


async def create_model_attitude(attitude_in: ModelAttitudeIn, session: AsyncSession) -> str:
    count_model_attributes = await session.execute(
        select(func.count(ModelResourceAttribute.id))
        .filter(or_(ModelResourceAttribute.id == attitude_in.left_attribute_id,
                    ModelResourceAttribute.id == attitude_in.right_attribute_id))
    )
    count_model_attributes = count_model_attributes.scalars().first()
    if count_model_attributes != 2:
        raise ModelAttitudeAttributesError()

    guid = str(uuid.uuid4())

    model_attitude = ModelAttitude(
        **attitude_in.dict(),
        guid=guid
    )

    session.add(model_attitude)
    await session.commit()

    model_attribute = await session.execute(
        select(ModelResourceAttribute)
        .where(ModelResourceAttribute.id == attitude_in.left_attribute_id)
    )
    model_attribute = model_attribute.scalars().first()

    model_resource = await session.execute(
        select(ModelResource)
        .where(ModelResource.id == model_attribute.resource_id)
    )
    model_resource = model_resource.scalars().first()
    await generate_version_number(id=model_resource.model_version_id, session=session, level=VersionLevel.MINOR)

    return model_attitude.guid


async def delete_model_attitude(guid: str, session: AsyncSession):
    model_attitude = await session.execute(
        select(ModelAttitude)
        .filter(ModelAttitude.guid == guid)
    )
    model_attitude = model_attitude.scalars().all()

    model_resource = await session.execute(
        delete(ModelResource)
        .where(ModelResource.guid == model_attitude.left_attribute_id)
    )
    model_resource = model_resource.scalars().first()
    await generate_version_number(id=model_resource.model_version_id, session=session, level=VersionLevel.MINOR)

    await session.execute(
        delete(ModelAttitude)
        .where(ModelAttitude.guid == guid)
    )
    await session.commit()