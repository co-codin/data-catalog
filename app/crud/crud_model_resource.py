import asyncio
import uuid

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.crud.crud_model_version import VersionLevel, generate_version_number
from app.errors.errors import AttributeDataTypeError, AttributeDataTypeOverflowError, ModelResourceHasAttributesError, \
    AttributeRelationError
from app.models.models import ModelResource, ModelResourceAttribute
from app.schemas.model_attribute import ResourceAttributeIn, ResourceAttributeUpdateIn, ModelResourceAttributeOut
from app.schemas.model_resource import ModelResourceIn, ModelResourceUpdateIn
from app.crud.crud_source_registry import add_tags, update_tags


async def check_attribute_for_errors(model_resource_attribute: ModelResourceAttribute, session: AsyncSession):
    if model_resource_attribute.db_link is None or model_resource_attribute.db_link == '':
        model_resource_attribute.db_link_error = True

    if model_resource_attribute.model_data_type_id is None and model_resource_attribute.model_resource_id is None:
        model_resource_attribute.data_type_errors = 'data_type_error'
    elif model_resource_attribute.model_resource_id is not None:
        model_resource = await session.execute(
            select(ModelResource)
            .options(selectinload(ModelResource.attributes))
            .filter(ModelResource.id == model_resource_attribute.model_resource_id)
        )
        model_resource = model_resource.scalars().first()
        if len(model_resource.attributes) == 0:
            model_resource_attribute.data_type_errors = 'nested_attribute_data_type_error'
        for model_resource_attribute in model_resource.attributes:
            await check_attribute_for_errors(model_resource_attribute=model_resource_attribute, session=session)

        await check_resource_for_errors(model_resource=model_resource)



async def check_resource_for_errors(model_resource: ModelResource):
    if model_resource.db_link is None or model_resource.db_link == '':
        model_resource.db_link_error = True
    else:
        model_resource.db_link_error = False

        print('111111111111111')
        print(model_resource.db_link_error)


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

    for attribute in model_resource.attributes:
        await check_attribute_for_errors(model_resource_attribute=attribute, session=session)
    await check_resource_for_errors(model_resource=model_resource)

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

    await generate_version_number(id=resource_in.model_version_id, session=session, level=VersionLevel.MINOR)

    return model_resource.guid


async def update_model_resource(guid: str, resource_update_in: ModelResourceUpdateIn, session: AsyncSession):
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
    model_resource = await session.execute(
        select(ModelResource)
        .where(ModelResource.guid == guid)
    )
    model_resource = model_resource.scalars().first()

    count_model_resource_attributes = await session.execute(
        select(func.count(ModelResourceAttribute.id))
        .filter(ModelResourceAttribute.resource_id == model_resource.id)
    )
    count_model_resource_attributes = count_model_resource_attributes.scalars().first()
    if count_model_resource_attributes > 0:
        raise ModelResourceHasAttributesError()

    await session.execute(
        delete(ModelResource)
        .where(ModelResource.guid == guid)
    )
    await session.commit()

    await generate_version_number(id=model_resource.model_version_id, session=session, level=VersionLevel.CRITICAL)


async def create_attribute(attribute_in: ResourceAttributeIn, session: AsyncSession):
    if (attribute_in.model_resource_id is None) and (attribute_in.model_data_type_id is None):
        raise AttributeDataTypeError()

    if (attribute_in.model_resource_id is not None) and (attribute_in.model_data_type_id is not None):
        raise AttributeDataTypeOverflowError()

    if attribute_in.model_resource_id == attribute_in.resource_id:
        raise AttributeRelationError()

    guid = str(uuid.uuid4())

    model_resource_attribute = ModelResourceAttribute(
        **attribute_in.dict(exclude={'tags', 'cardinality'}),
        guid=guid
    )

    if attribute_in.cardinality is not None:
        model_resource_attribute.cardinality = attribute_in.cardinality.value

    await add_tags(model_resource_attribute, attribute_in.tags, session)

    session.add(model_resource_attribute)
    await session.commit()

    model_resource = await session.execute(
        select(ModelResource)
        .where(ModelResource.id == model_resource_attribute.resource_id)
    )
    model_resource = model_resource.scalars().first()
    await generate_version_number(id=model_resource.model_version_id, session=session, level=VersionLevel.MINOR)

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

    await check_attribute_for_errors(model_resource_attribute=model_resource_attribute, session=session)
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

    model_resource = await session.execute(
        select(ModelResource)
        .where(ModelResource.id == model_resource_attribute.resource_id)
    )
    model_resource = model_resource.scalars().first()
    await generate_version_number(id=model_resource.model_version_id, session=session, level=VersionLevel.CRITICAL)

    await session.execute(
        delete(ModelResourceAttribute)
        .where(ModelResourceAttribute.guid == guid)
    )
