from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.errors.model_version import (
    ModelVersionDBLinkError, ModelVersionDataTypeError, ModelVersionNestedAttributeDataTypeError,
    ModelVersionEmptyResourceError, ModelVersionAttributeDBLinkError
)
from app.models import Object, Field
from app.models.models import ModelVersion, ModelResource, ModelResourceAttribute


def init_model_resource_errors(model_resource: ModelResource):
    if not hasattr(model_resource, 'errors'):
        setattr(model_resource, 'errors', [])


objects = []
fields = []


async def get_objects_list(session: AsyncSession) -> list:
    global objects
    if not len(objects):
        objects = await session.execute(
            select(Object.db_path)
        )
        objects = objects.scalars().all()

    return objects


async def get_fields_list(session: AsyncSession) -> list:
    global fields
    if not len(fields):
        fields = await session.execute(
            select(Field.db_path)
        )
        fields = fields.scalars().all()

    return fields


async def check_model_resources_error(model_version: ModelVersion, session: AsyncSession):
    exist_errors = {}
    for model_resource in model_version.model_resources:
        await check_resource_for_errors(model_resource=model_resource, session=session)
        for error in model_resource.errors:
            exist_errors[error] = True

    if 'db_link_error' in exist_errors:
        raise ModelVersionDBLinkError()

    if 'empty_resource' in exist_errors:
        raise ModelVersionEmptyResourceError()

    if 'data_type_error' in exist_errors:
        raise ModelVersionDataTypeError()

    if 'nested_attribute_data_type_error' in exist_errors:
        raise ModelVersionNestedAttributeDataTypeError()

    if 'attribute_db_link_error' in exist_errors:
        raise ModelVersionAttributeDBLinkError()


async def check_resource_for_errors(model_resource: ModelResource, session: AsyncSession):
    objects = await get_objects_list(session=session)
    init_model_resource_errors(model_resource=model_resource)

    for attribute in model_resource.attributes:
        error = await check_attribute_for_errors(model_resource_attribute=attribute, session=session)
        model_resource.errors.append(error) if error not in model_resource.errors else model_resource.errors
        model_resource.errors.append(error)

    if model_resource.db_link is None or model_resource.db_link == '':
        model_resource.errors.append('db_link_error')
    elif model_resource.db_link not in objects:
        model_resource.errors.append('db_link_error')

    if len(model_resource.attributes) == 0:
        model_resource.errors.append('empty_resource')

    errors = []
    for err in model_resource.errors:
        if err not in errors:
            errors.append(err)
    model_resource.errors = errors


async def check_attribute_for_errors(model_resource_attribute: ModelResourceAttribute,
                                     session: AsyncSession) -> str | None:
    fields = await get_fields_list(session=session)
    if model_resource_attribute.db_link is None or model_resource_attribute.db_link == '':
        model_resource_attribute.db_link_error = True
        return 'attribute_db_link_error'
    elif model_resource_attribute.db_link not in fields:
        model_resource_attribute.db_link_error = True
        return 'attribute_db_link_error'

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

        await check_resource_for_errors(model_resource=model_resource, session=session)

    if hasattr(model_resource_attribute, 'data_type_errors'):
        return model_resource_attribute.data_type_errors
    return None
