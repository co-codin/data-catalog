import asyncio
import uuid

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, load_only

from fastapi import HTTPException, status

from age import Age

from app.age_queries.node_queries import match_model_resource_rels, set_link_between_nodes, delete_link_between_nodes
from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.crud.crud_model_version import generate_version_number
from app.enums.enums import ModelVersionLevel
from app.errors.checker import check_resource_for_errors, check_attribute_for_errors, init_model_resource_errors
from app.errors.errors import (
    AttributeDataTypeError, AttributeDataTypeOverflowError, ModelResourceHasAttributesError,
    AttributeRelationError, ModelAttitudeAttributesError
)
from app.models.models import ModelResource, ModelResourceAttribute
from app.schemas.model_resource_rel import ModelResourceRelOut, ModelResourceRelIn
from app.schemas.model_attribute import ResourceAttributeIn, ResourceAttributeUpdateIn, ModelResourceAttributeOut
from app.schemas.model_resource import ModelResourceIn, ModelResourceUpdateIn
from app.crud.crud_source_registry import add_tags, update_tags
from app.constants.data_types import ID_TO_SYS_DATA_TYPE
from app.schemas.model_attribute import ModelResourceAttrOutRelIn


async def read_resources_by_version_id(version_id: int, session: AsyncSession):
    model_resources = await session.execute(
        select(ModelResource)
        .options(selectinload(ModelResource.tags))
        .options(selectinload(ModelResource.comments))
        .options(selectinload(ModelResource.attributes))
        .filter(ModelResource.model_version_id == version_id)
    )
    model_resources = model_resources.scalars().all()
    for model_resource in model_resources:
        await check_resource_for_errors(model_resource=model_resource, session=session)

    return model_resources


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

    await check_resource_for_errors(model_resource=model_resource, session=session)

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

    await generate_version_number(id=resource_in.model_version_id, session=session, level=ModelVersionLevel.MINOR)

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

    await generate_version_number(id=model_resource.model_version_id, session=session, level=ModelVersionLevel.CRITICAL)


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
    await generate_version_number(id=model_resource.model_version_id, session=session, level=ModelVersionLevel.MINOR)

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

    error = await check_attribute_for_errors(model_resource_attribute=model_resource_attribute, session=session)
    if error:
        init_model_resource_errors(model_resource=model_resource_attribute.resources)
        model_resource_attribute.resources.errors.append(error)

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
    await generate_version_number(id=model_resource.model_version_id, session=session, level=ModelVersionLevel.CRITICAL)

    await session.execute(
        delete(ModelResourceAttribute)
        .where(ModelResourceAttribute.guid == guid)
    )


async def read_model_resource_attrs(guid: str, session: AsyncSession) -> list[ModelResourceAttrOutRelIn]:
    model_resource = await session.execute(
        select(ModelResource)
        .options(selectinload(ModelResource.attributes))
        .where(ModelResource.guid == guid)
    )
    model_resource = model_resource.scalars().first()
    if not model_resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return [
        ModelResourceAttrOutRelIn(
            name=attr.name, type=ID_TO_SYS_DATA_TYPE.get(attr.model_data_type_id, None), key=attr.key
        )
        for attr in model_resource.attributes
    ]


async def read_model_resource_rels(guid: str, session: AsyncSession, age_session: Age) -> list[ModelResourceRelOut]:
    model_resource = await session.execute(
        select(ModelResource)
        .options(load_only(ModelResource.name, ModelResource.db_link))
        .where(ModelResource.guid == guid)
    )
    model_resource = model_resource.scalars().first()
    if not model_resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="model resource doesn't exist")

    graph_name = model_resource.db_link.rsplit('.', maxsplit=1)[0]
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _read_model_resource_rels, graph_name, model_resource.name, age_session
    )


def _read_model_resource_rels(graph_name: str, model_resource_name: str, age_session: Age) -> list[ModelResourceRelOut]:
    age_session.setGraph(graph_name)
    cursor = age_session.execCypher(
        match_model_resource_rels,
        cols=['rel', 't2_name', 'one_to_many_id'],
        params=(model_resource_name,)
    )
    return [
        ModelResourceRelOut(
            resource_attr=model_resource_rel[0][1], mapped_resource=model_resource_rel[1],
            key_attr=model_resource_rel[0][0], gid=model_resource_rel[2]
        )
        for model_resource_rel in cursor
    ]


async def create_model_resource_rel(
        guid: str, rel_in: ModelResourceRelIn, session: AsyncSession, age_session: Age
) -> tuple[int, int]:
    model_resources = await session.execute(
        select(ModelResource)
        .options(
            load_only(ModelResource.guid, ModelResource.name, ModelResource.db_link, ModelResource.model_version_id)
        )
        .where(ModelResource.guid.in_((guid, rel_in.mapped_resource_guid)))
    )
    model_resources = model_resources.scalars().all()

    if model_resources[0].guid == guid:
        resource = model_resources[0]
        mapped_resource = model_resources[1]
    else:
        resource = model_resources[1]
        mapped_resource = model_resources[0]

    graph_name = resource.db_link.rsplit('.', maxsplit=1)[0]
    loop = asyncio.get_running_loop()
    one_to_many_rel_id = await loop.run_in_executor(
        None, _create_model_resource_rel, graph_name, mapped_resource.name, resource.name,
        rel_in.mapped_resource_key_attr, rel_in.resource_attr, age_session
    )

    return one_to_many_rel_id, resource.model_version_id


def _create_model_resource_rel(
        graph_name: str, mapped_resource_name: str, resource_name: str,
        mapped_resource_key_attr: str, resource_attr: str, age_session: Age
) -> int:
    age_session.setGraph(graph_name)
    cursor = age_session.execCypher(
        set_link_between_nodes,
        cols=['r_one_to_many_id'],
        params=(
            mapped_resource_name, resource_name,
            mapped_resource_key_attr, resource_attr,
            resource_attr, mapped_resource_key_attr
        )
    )
    one_to_many_rel_id = next(cursor)[0]
    return one_to_many_rel_id


async def check_on_model_resources_len(resource_guid: str, mapped_resource_guid: str, session: AsyncSession) -> None:
    model_resources_count = await session.execute(
        select(func.count(ModelResource.id))
        .where(ModelResource.guid.in_(
            (resource_guid, mapped_resource_guid))
        )
    )
    model_resources_count = model_resources_count.scalars().first()
    if model_resources_count != 2:
        raise ModelAttitudeAttributesError()


def remove_model_resource_rel(gid: int, graph_name: str, age_session: Age) -> None:
    age_session.setGraph(graph_name)
    age_session.execCypher(
        delete_link_between_nodes,
        cols=['r_one_to_many BIGINT'],
        params=(gid,)
    )


async def read_model_resource(resource_guid: str, session: AsyncSession) -> ModelResource:
    model_resource = await session.execute(
        select(ModelResource)
        .options(load_only(ModelResource.db_link, ModelResource.model_version_id))
        .where(ModelResource.guid == resource_guid)
    )
    model_resource = model_resource.scalars().first()
    if not model_resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="model resource doesn't exist")
    return model_resource

