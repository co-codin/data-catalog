import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status

from app.crud.crud_model_version import generate_version_number
from app.enums.enums import ModelVersionLevel, ModelVersionStatus
from app.errors.errors import OperationParameterNotExistError, OperationParameterNotConfiguredError, \
    OperationParameterOutputError
from app.errors.model_version import ModelVersionNotDraftError
from app.models.models import ModelRelation, ModelVersion, OperationBody, Operation, \
    ModelRelationOperation, ModelRelationOperationParameter
from app.schemas.model_relation import ModelRelationIn, ModelRelationUpdateIn, ModelRelationOperationIn, \
    ModelRelationOperationUpdateIn, \
    ModelRelationOperationParameterIn, ModelRelationOperationParameterUpdateIn
from app.crud.crud_source_registry import add_tags, update_tags


async def read_relations_by_version(version_id: int, session: AsyncSession):
    model_relation = await session.execute(
        select(ModelRelation)
        .filter(ModelRelation.model_version_id == version_id)
    )
    model_relation = model_relation.scalars().all()
    return model_relation


async def fill_nested_operations(relation_operation: ModelRelationOperation, session: AsyncSession):

    for model_relation_operation_parameter in relation_operation.model_relation_operation_parameters:
        if model_relation_operation_parameter.model_resource_attribute_id is None and model_relation_operation_parameter.value is None:
            inner_model_operation = await session.execute(
                select(ModelRelationOperation)
                .options(selectinload(ModelRelationOperation.model_relation_operation_parameters).selectinload(ModelRelationOperation.operations_bodies))
                .filter(ModelRelationOperation.parent_id == model_relation_operation_parameter.model_relation_operation_id)
            )
            model_relation_operation_parameter.inner_operation = inner_model_operation.scalars().first()
            await fill_nested_operations(relation_operation=model_relation_operation_parameter.inner_operation, session=session)
            await check_newest_version_exists(operation_body=inner_model_operation.relation_operation.operations_bodies,
                                              session=session)


async def check_newest_version_exists(operation_body: OperationBody, session: AsyncSession):
    latest_operation_version = await session.execute(
        select(OperationBody.version)
        .filter(OperationBody.operation_id == operation_body.operation_id)
        .order_by(OperationBody.version.desc())
    )
    latest_operation_version = latest_operation_version.scalars().first()
    if latest_operation_version > operation_body.version:
        operation_body.new_version_exists = True

async def read_relation_by_guid(guid: str, session: AsyncSession):
    model_relation = await session.execute(
        select(ModelRelation)
        .options(selectinload(ModelRelation.tags))
        .options(joinedload(ModelRelation.relation_operation).selectinload(ModelRelationOperation.model_relation_operation_parameters))
        .options(joinedload(ModelRelation.relation_operation).selectinload(ModelRelationOperation.operations_bodies))
        .filter(ModelRelation.guid == guid)
    )
    model_relation = model_relation.scalars().first()

    await fill_nested_operations(relation_operation=model_relation.relation_operation, session=session)
    await check_newest_version_exists(operation_body=model_relation.relation_operation.operations_bodies,
                                      session=session)


    if not model_relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return model_relation


async def check_model_version_is_draft(version_id: int, session: AsyncSession):
    model_version = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.id == version_id)
    )
    model_version = model_version.scalars().first()

    if model_version.status != ModelVersionStatus.DRAFT.value:
        raise ModelVersionNotDraftError


def check_model_relation_operation_parameter(model_relation_operation_parameter_in: ModelRelationOperationParameterIn
                                                                                    | ModelRelationOperationParameterUpdateIn):
    test = int(model_relation_operation_parameter_in.value is not None) \
           + int(model_relation_operation_parameter_in.model_resource_attribute_id is not None) \
           + int(model_relation_operation_parameter_in.model_relation_operation is not None)
    if test != 1:
        raise OperationParameterNotConfiguredError()


async def check_model_relation_operation_in(
        model_relation_operation_in: ModelRelationOperationIn | ModelRelationOperationUpdateIn | None,
        session: AsyncSession):
    if model_relation_operation_in is None:
        return

    operation_body = await session.execute(
        select(OperationBody)
        .options(selectinload(OperationBody.operation_body_parameters))
        .filter(OperationBody.operation_body_id == model_relation_operation_in.operation_body_id)
    )
    operation_body = operation_body.scalars().first()

    operation = await session.execute(
        select(Operation)
        .filter(Operation.operation_id == operation_body.operation_id)
    )
    operation = operation.scalars().first()

    for operation_body_parameter in operation_body.operation_body_parameters:
        found = False
        for model_relation_operation_parameter_in in model_relation_operation_in.model_relation_operation_parameter:
            if model_relation_operation_parameter_in.operation_body_parameter_id == operation_body_parameter.operation_body_parameter_id:
                check_model_relation_operation_parameter(
                    model_relation_operation_parameter_in=model_relation_operation_parameter_in)
                found = True
                if not operation_body_parameter.flag and model_relation_operation_parameter_in.model_resource_attribute_id is None:
                    raise OperationParameterOutputError(id_=operation_body_parameter.operation_body_parameter_id,
                                                        name=operation_body_parameter.name)

        if not found:
            raise OperationParameterNotExistError(parameter=operation_body_parameter.name, operation=operation.name,
                                                  version=operation_body.version)

        if hasattr(operation_body_parameter, 'model_relation_operation'):
            await check_model_relation_operation_in(
                model_relation_operation_in=operation_body_parameter.model_relation_operation,
                session=session)


async def create_model_relation_operation(model_relation_id: int | None,
                                          model_relation_operation_in: ModelRelationOperationIn | ModelRelationOperationUpdateIn | None,
                                          session: AsyncSession, parent_id: int | None):
    if model_relation_operation_in is None:
        return

    guid = str(uuid.uuid4())
    model_relation_operation = ModelRelationOperation(
        guid=guid,
        model_relation_id=model_relation_id,
        operation_body_id=model_relation_operation_in.operation_body_id,
        parent_id=parent_id
    )
    session.add(model_relation_operation)
    await session.commit()

    for model_relation_operation_parameter_in in model_relation_operation_in.model_relation_operation_parameter:
        guid = str(uuid.uuid4())
        model_relation_operation_parameter = ModelRelationOperationParameter(
            guid=guid,
            model_relation_operation_id=model_relation_operation.id,
            model_resource_attribute_id=model_relation_operation_parameter_in.model_resource_attribute_id,
            value=model_relation_operation_parameter_in.value
        )
        session.add(model_relation_operation_parameter)
        await session.commit()

        if model_relation_operation_parameter_in.model_relation_operation is not None:
            if type(model_relation_operation_parameter_in.model_relation_operation) == dict:
                model_relation_operation_parameter_in.model_relation_operation = ModelRelationOperationIn(
                    **model_relation_operation_parameter_in.model_relation_operation
                )
            await create_model_relation_operation(model_relation_id=None,
                                                  model_relation_operation_in=model_relation_operation_parameter_in.model_relation_operation,
                                                  session=session, parent_id=model_relation_operation.id)


async def create_model_relation(relation_in: ModelRelationIn, session: AsyncSession) -> str:
    await check_model_version_is_draft(version_id=relation_in.model_version_id, session=session)

    await check_model_relation_operation_in(model_relation_operation_in=relation_in.model_relation_operation,
                                            session=session)

    guid = str(uuid.uuid4())
    model_relation = ModelRelation(
        **relation_in.dict(exclude={'tags', 'model_relation_operation'}),
        guid=guid
    )
    await add_tags(model_relation, relation_in.tags, session)
    session.add(model_relation)
    await session.commit()

    await create_model_relation_operation(model_relation_id=model_relation.id,
                                          model_relation_operation_in=relation_in.model_relation_operation,
                                          session=session, parent_id=None)

    await generate_version_number(id=model_relation.model_version_id, session=session, level=ModelVersionLevel.PATCH)
    return model_relation.guid


async def update_model_relation_operation_parameter(
        model_relation_operation_parameter_in: ModelRelationOperationParameterUpdateIn | None,
        session: AsyncSession):
    if model_relation_operation_parameter_in is None:
        return

    check_model_relation_operation_parameter(
        model_relation_operation_parameter_in=model_relation_operation_parameter_in)
    await session.execute(
        update(ModelRelationOperationParameter)
        .where(
            ModelRelationOperationParameter.id == model_relation_operation_parameter_in.model_relation_operation_parameter_id)
        .values(
            model_resource_attribute_id=model_relation_operation_parameter_in.model_resource_attribute_id,
            value=model_relation_operation_parameter_in.value,
        )
    )

    await update_model_relation_operation(
        model_relation_operation_in=model_relation_operation_parameter_in.model_relation_operation,
        session=session)


async def update_model_relation_operation(model_relation_operation_in: ModelRelationOperationUpdateIn | None,
                                          session: AsyncSession):
    if model_relation_operation_in is None:
        return

    for model_relation_operation_parameter_in in model_relation_operation_in.model_relation_operation_parameter:
        if type(model_relation_operation_parameter_in.model_relation_operation) == dict:
            model_relation_operation_parameter_in.model_relation_operation = ModelRelationOperationIn(
                **model_relation_operation_parameter_in.model_relation_operation
            )
        await update_model_relation_operation_parameter(
            model_relation_operation_parameter_in=model_relation_operation_parameter_in,
            session=session)


async def update_model_relation(guid: str, relation_update_in: ModelRelationUpdateIn, session: AsyncSession):
    model_relation = await session.execute(
        select(ModelRelation)
        .options(selectinload(ModelRelation.tags))
        .filter(ModelRelation.guid == guid)
    )
    model_relation = model_relation.scalars().first()

    if not model_relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    model_relation_update_in_data = {
        key: value for key, value in relation_update_in.dict(exclude={'tags', 'model_relation_operation'}).items()
        if value is not None
    }

    await session.execute(
        update(ModelRelation)
        .where(ModelRelation.guid == guid)
        .values(
            **model_relation_update_in_data,
        )
    )

    await update_tags(model_relation, session, relation_update_in.tags)

    if relation_update_in.model_relation_operation.model_relation_operation_id is not None:
        await update_model_relation_operation(model_relation_operation_in=relation_update_in.model_relation_operation,
                                              session=session)
    elif relation_update_in.model_relation_operation.operation_body_id:
        await check_model_relation_operation_in(model_relation_operation_in=relation_update_in.model_relation_operation,
                                                session=session)
        await session.execute(
            delete(ModelRelationOperation)
            .where(ModelRelationOperation.model_relation_id == model_relation.id)
        )
        await create_model_relation_operation(model_relation_id=model_relation.id,
                                              model_relation_operation_in=relation_update_in.model_relation_operation,
                                              session=session, parent_id=None)


async def delete_child_operations(parent_id: int, session: AsyncSession):
    children = await session.execute(
        select(ModelRelationOperation)
        .filter(ModelRelationOperation.parent_id == parent_id)
    )
    children = children.scalars().first()
    for child in children:
        await delete_child_operations(parent_id=child.id, session=session)
        await session.execute(
            delete(ModelRelationOperation)
            .where(ModelRelationOperation.guid == parent_id)
        )


async def delete_model_relation(guid: str, session: AsyncSession):
    model_relation = await session.execute(
        select(ModelRelation)
        .options(selectinload(ModelRelation.tags))
        .filter(ModelRelation.guid == guid)
    )
    model_relation = model_relation.scalars().first()

    await check_model_version_is_draft(version_id=model_relation.model_version_id, session=session)
    await generate_version_number(id=model_relation.model_version_id, session=session, level=ModelVersionLevel.PATCH)

    model_relation_operation = await session.execute(
        select(ModelRelationOperation)
        .filter(ModelRelationOperation.model_relation_id == model_relation.id)
    )
    model_relation_operation = model_relation_operation.scalars().first()
    await delete_child_operations(parent_id=model_relation_operation.id, session=session)
    await session.execute(
        delete(ModelRelation)
        .where(ModelRelation.guid == guid)
    )
