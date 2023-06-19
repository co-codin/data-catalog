import uuid
import asyncio

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import Optional

from app.crud.crud_tag import add_tags, update_tags
from app.errors.errors import OperationNameAlreadyExist, OperationInputParametersNotExists, \
    OperationOutputParameterNotExists, OperationParametersNameAlreadyExist
from app.models.operations import Operation, OperationBody, OperationBodyParameter
from app.schemas.operation import OperationOut, OperationParameterIn, OperationIn, OperationUpdateIn


async def read_all(session: AsyncSession) -> list[OperationOut]:
    operations = await session.execute(
        select(Operation)
        .options(selectinload(Operation.tags))
        .options(joinedload(Operation.operation_body).selectinload(OperationBody.operation_body_parameters))
        .order_by(Operation.created_at)
    )
    operations = operations.scalars().all()
    return [OperationOut.from_orm(operation) for operation in operations]


async def read_by_guid(guid: str, session: AsyncSession) -> OperationOut:
    operation = await session.execute(
        select(Operation)
        .options(selectinload(Operation.tags))
        .options(joinedload(Operation.operation_body).selectinload(OperationBody.operation_body_parameters))
        .filter(Operation.guid == guid)
    )

    operation = operation.scalars().first()

    if not operation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    operation_out = OperationOut.from_orm(operation)

    return operation_out


async def create_operation(operation_in: OperationIn, session: AsyncSession, token: str) -> Operation:
    guid = str(uuid.uuid4())

    operation_body = OperationBody(
        code=operation_in.code,
        guid=guid,

    )
    session.add(operation_body)

    if not OperationIn.owner:
        pass

    operation = Operation(
        **operation_in.dict(exclude={'tags', 'code', 'parameters'}),
        guid=guid,
        operation_body_id=operation_body.id
    )
    session.add(operation)

    await add_tags(operation, operation_in.tags, session)

    for parameter_in in operation_in.parameters:
        guid = str(uuid.uuid4())
        parameter = OperationBodyParameter(
            **parameter_in.dict(),
            guid=guid,
            operation_body_id=operation_body.id
        )
        session.add(parameter)

    return operation


async def edit_operation(guid: str, operation_update_in: OperationUpdateIn, session: AsyncSession):
    operation_update_in_data = {
        key: value for key, value in operation_update_in.dict(exclude={'tags', 'code', 'parameters'}).items()
        if value is not None
    }

    await session.execute(
        update(Operation)
        .where(Operation.guid == guid)
        .values(
            **operation_update_in_data,
        )
    )

    operation = await session.execute(
        select(Operation)
        .options(selectinload(Operation.tags))
        .filter(Operation.guid == guid)
    )
    operation = operation.scalars().first()
    if not operation:
        return

    await update_tags(operation, session, operation_update_in.tags)

    await session.execute(
        update(OperationBody)
        .where(OperationBody.guid == guid)
        .values(
            code=operation_update_in.code
        )
    )

    operation_body = await session.execute(
        select(OperationBody)
        .selectinload(OperationBody.operation_body_parameters)
        .filter(OperationBody.guid == guid)
    )

    if operation_update_in.parameters is not None:
        parameters_update_in_set = {parameter for parameter in operation_update_in.parameters}
        body_parameters_set = {parameter.name for parameter in operation_body.operation_body_parameters}
        body_parameters_dict = {parameter.name: parameter for parameter in operation_body.operation_body_parameters}

        parameters_to_delete = body_parameters_set - parameters_update_in_set
        for parameter in parameters_to_delete:
            operation_body.operation_body_parameters.remove(body_parameters_dict[parameter])

        parameters__to_create = parameters_update_in_set - body_parameters_set
        for parameter_in in parameters__to_create:
            guid = str(uuid.uuid4())
            parameter = OperationBodyParameter(
                **parameter_in.dict(),
                guid=guid,
                operation_body_id=operation_body.id
            )
            session.add(parameter)


async def delete_by_guid(guid: str, session: AsyncSession):
    await session.execute(
        delete(Operation)
        .where(Operation.guid == guid)
    )
    await session.commit()


async def check_on_operation_name_uniqueness(name: str, session: AsyncSession, guid: Optional[str] = None):
    operations = await session.execute(
        select(Operation)
        .where(Operation.name == name)
    )
    operations = operations.scalars().all()
    for operation in operations:
        if operation.name == name and operation.guid != guid:
            raise OperationNameAlreadyExist(name)


async def check_on_operation_parameters_uniqueness(parameters: list[OperationParameterIn], session: AsyncSession, guid: Optional[str] = None):
    list_parameters_in = []
    list_parameters_out = []
    for parameter in parameters:
        if parameter.flag:
            list_parameters_in.append(parameter.name)
        else:
            list_parameters_out.append(parameter.name)

    operation_body = await session.execute(
        select(OperationBody)
        .selectinload(OperationBody.operation_body_parameters)
        .filter(OperationBody.guid == guid)
    )
    operation_body = operation_body.scalars().first()
    for parameter in operation_body.operation_body_parameters:
        if parameter.flag:
            list_parameters_in.append(parameter.name)
        else:
            list_parameters_out.append(parameter.name)

    if not len(list_parameters_in):
        raise OperationInputParametersNotExists()

    if len(list_parameters_out) != 1:
        raise OperationOutputParameterNotExists()

    set_parameters_in = set(list_parameters_in)
    if len(list_parameters_in) != len(set_parameters_in):
        raise OperationParametersNameAlreadyExist()

