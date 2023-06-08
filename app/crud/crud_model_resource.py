import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.model import ModelResource, ModelResourceAttribute
from app.schemas.model_resource import ModelResourceIn, ModelResourceUpdateIn, ResourceAttributeIn, \
    ResourceAttributeUpdateIn
from app.crud.crud_source_registry import add_tags, update_tags


async def read_resources_by_version_id(version_id: int, session: AsyncSession):
    model_resource = await session.execute(
        select(ModelResource)
        .filter(ModelResource.model_version_id == version_id)
    )
    model_resource = model_resource.scalars().all()
    return model_resource


async def read_resources_by_guid(guid: str, token: str, session: AsyncSession):
    model_resource = await session.execute(
        select(ModelResource)
        .options(selectinload(ModelResource.tags))
        .options(selectinload(ModelResource.comments))
        .filter(ModelResource.guid == guid)
    )

    model_resource = model_resource.scalars().first()

    if not model_resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return model_resource


async def create_model_resource(resource_in: ModelResourceIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())

    model_resource = ModelResource(
        **resource_in.dict(exclude={'tags'}),
        guid=guid
    )
    await add_tags(model_resource, resource_in.tags, session)

    session.add(model_resource)
    await session.commit()

    return model_resource.guid


async def update_model_resource(guid: int, resource_update_in: ModelResourceUpdateIn, session: AsyncSession):
    model_resource = await session.execute(
        select(ModelResource)
        .options(selectinload(ModelResource.tags))
        .filter(ModelResource.guid == guid)
    )
    model_resource = model_resource.scalars().first()

    model_resource_update_in_data = {
        key: value for key, value in resource_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    await session.execute(
        update(ModelResource)
        .where(ModelResource.guid == guid)
        .values(
            **model_resource_update_in_data,
        )
    )

    await update_tags(model_resource, session, resource_update_in.tags)

    session.add(model_resource)
    await session.commit()


async def delete_model_resource(guid: str, session: AsyncSession):
    await session.execute(
        delete(ModelResource)
        .where(ModelResource.guid == guid)
    )
    await session.commit()


async def create_attribute(attribute_in: ResourceAttributeIn, session=AsyncSession):
    guid = str(uuid.uuid4())

    model_resource_attribute = ModelResourceAttribute(
        **attribute_in.dict(exclude={'tags'}),
        guid=guid,
    )

    await add_tags(model_resource_attribute, attribute_in.tags, session)

    session.add(model_resource_attribute)
    await session.commit()

    return model_resource_attribute.guid


async def edit_attribute(guid: str, attribute_update_in: ResourceAttributeUpdateIn, session=AsyncSession):
    model_resource_attribute = await session.execute(
        select(ModelResourceAttribute)
        .options(selectinload(ModelResourceAttribute.tags))
        .filter(ModelResource.guid == guid)
    )
    model_resource_attribute = model_resource_attribute.scalars().first()

    model_resource_attribute_update_in_data = {
        key: value for key, value in attribute_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    await session.execute(
        update(ModelResourceAttribute)
        .where(ModelResourceAttribute.guid == guid)
        .values(
            **model_resource_attribute_update_in_data,
        )
    )

    await update_tags(model_resource_attribute, session, attribute_update_in.tags)


async def delete_children(parent_id: int, session: AsyncSession):
    children_model_resource_attributes = await session.execute(
        select(ModelResourceAttribute)
        .filter(ModelResourceAttribute.parent_id == parent_id)
    )
    children_model_resource_attributes = children_model_resource_attributes.scalars().all()
    for children_model_resource_attribute in children_model_resource_attributes:
        await delete_children(children_model_resource_attribute.id, session)

    await session.execute(
        delete(ModelResourceAttribute)
        .where(ModelResourceAttribute.parent_id == parent_id)
    )


async def remove_attribute(guid: str, session: AsyncSession):
    model_resource_attribute = await session.execute(
        select(ModelResourceAttribute)
        .filter(ModelResourceAttribute.guid == guid)
    )
    model_resource_attribute = model_resource_attribute.scalars().first()

    await delete_children(model_resource_attribute.id, session)

    await session.execute(
        delete(ModelResourceAttribute)
        .where(ModelResourceAttribute.guid == guid)
    )
    await session.commit()
