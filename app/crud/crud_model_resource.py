import asyncio
import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.errors.errors import AttributeDataTypeError, AttributeDataTypeOverflowError
from app.models.models import ModelResource, ModelResourceAttribute, ModelDataType
from app.schemas.model_attribute import ResourceAttributeIn, ResourceAttributeUpdateIn, ModelResourceAttributeOut
from app.schemas.model_resource import ModelResourceIn, ModelResourceUpdateIn
from app.crud.crud_source_registry import add_tags, update_tags


async def read_resources_by_version_id(version_id: int, session: AsyncSession):
    model_resource = await session.execute(
        select(ModelResource)
        .options(selectinload(ModelResource.tags))
        .options(selectinload(ModelResource.comments))
        .filter(ModelResource.model_version_id == version_id)
    )
    model_resource = model_resource.scalars().all()

    return model_resource


async def read_resources_by_guid(guid: str, token: str, session: AsyncSession):
    model_resource = await session.execute(
        select(ModelResource)
        .options(selectinload(ModelResource.tags))
        .options(selectinload(ModelResource.comments))
        .options(selectinload(ModelResource.attributes).selectinload(ModelResourceAttribute.model_data_types))
        .filter(ModelResource.guid == guid)
    )

    model_resource = model_resource.scalars().first()

    if not model_resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if model_resource.comments:
        author_guids = {comment.author_guid for comment in model_resource.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, get_authors_data_by_guids, author_guids, token
        )
        set_author_data(model_resource.comments, authors_data)

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


async def create_attribute(attribute_in: ResourceAttributeIn, session: AsyncSession):
    if (attribute_in.model_resource_id is None) and (attribute_in.model_data_type_id is None):
        raise AttributeDataTypeError()

    if (attribute_in.model_resource_id is not None) and (attribute_in.model_data_type_id is not None):
        raise AttributeDataTypeOverflowError()

    guid = str(uuid.uuid4())

    model_resource_attribute = ModelResourceAttribute(
        **attribute_in.dict(exclude={'tags', 'cardinality'}),
        guid=guid,
        cardinality=attribute_in.cardinality.value,
    )

    await add_tags(model_resource_attribute, attribute_in.tags, session)

    session.add(model_resource_attribute)
    await session.commit()

    return model_resource_attribute.guid


async def get_attribute_parents(session: AsyncSession, parents: list, parent_id: int):
    model_resource_attribute = await session.execute(
        select(ModelResourceAttribute)
        .options(selectinload(ModelResourceAttribute.resources))
        .options(selectinload(ModelResourceAttribute.model_resources))
        .options(selectinload(ModelResourceAttribute.model_data_types))
        .options(selectinload(ModelResourceAttribute.tags))
        .options(selectinload(ModelResourceAttribute.resources))
        .filter(ModelResourceAttribute.id == parent_id)
    )
    model_resource_attribute = model_resource_attribute.scalars().first()

    parents.append(model_resource_attribute)

    if model_resource_attribute.parent_id is None:
        return parents

    parents = await get_attribute_parents(session=session, parents=parents,
                                          parent_id=model_resource_attribute.parent_id)
    return parents


async def get_attribute_by_guid(guid: str, session: AsyncSession):
    model_resource_attribute = await session.execute(
        select(ModelResourceAttribute)
        .options(selectinload(ModelResourceAttribute.resources))
        .options(selectinload(ModelResourceAttribute.model_resources))
        .options(selectinload(ModelResourceAttribute.model_data_types))
        .options(selectinload(ModelResourceAttribute.tags))
        .options(selectinload(ModelResourceAttribute.resources))
        .filter(ModelResourceAttribute.guid == guid)
    )
    model_resource_attribute = model_resource_attribute.scalars().first()

    if not model_resource_attribute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    model_resource_attribute_out = ModelResourceAttributeOut.from_orm(model_resource_attribute)

    if model_resource_attribute.parent_id is not None:
        parents = await get_attribute_parents(session=session, parents=[], parent_id=model_resource_attribute.parent_id)
        model_resource_attribute_out.parents = parents

    return model_resource_attribute_out


async def edit_attribute(guid: str, attribute_update_in: ResourceAttributeUpdateIn, session: AsyncSession):
    model_resource_attribute = await session.execute(
        select(ModelResourceAttribute)
        .options(selectinload(ModelResourceAttribute.tags))
        .filter(ModelResourceAttribute.guid == guid)
    )
    model_resource_attribute = model_resource_attribute.scalars().first()

    model_resource_attribute_update_in_data = {
        key: value for key, value in
        attribute_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    if (attribute_update_in.model_resource_id is not None) and (attribute_update_in.model_data_type_id is not None):
        raise AttributeDataTypeOverflowError()

    if (model_resource_attribute.model_resource_id is not None) and (attribute_update_in.model_resource_id is None):
        model_resource_attribute_update_in_data['model_resource_id'] = None

    if (model_resource_attribute.model_data_type_id is not None) and (attribute_update_in.model_data_type_id is None):
        model_resource_attribute_update_in_data['model_data_type_id'] = None

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
