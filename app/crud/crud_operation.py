import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import Optional

from app.crud.crud_tag import add_tags, update_tags
from app.errors.errors import OperationNameAlreadyExist, OperationInputParametersNotExists, \
    OperationOutputParameterNotExists, OperationParametersNameAlreadyExist
from app.models.models import Operation, OperationBody, OperationBodyParameter
from app.schemas.operation import OperationOut, OperationParameterIn, OperationIn, OperationUpdateIn, OperationManyOut


async def read_all(session: AsyncSession) -> list[OperationManyOut]:
    operations = await session.execute(
        select(Operation)
        .options(selectinload(Operation.tags))
        .order_by(Operation.created_at)
    )
    operations = operations.scalars().all()
    return [OperationManyOut.from_orm(operation) for operation in operations]


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


async def create_operation_version(version: int, operation_id: int, data_in: OperationIn | OperationUpdateIn,
                                   session: AsyncSession, author_guid=""):
    guid = str(uuid.uuid4())
    operation_body = OperationBody(
        code=data_in.code,
        guid=guid,
        operation_id=operation_id,
        version=version
    )

    if isinstance(data_in, OperationUpdateIn):
        operation_body.version_desc = data_in.version_desc
        if data_in.version_owner is None:
            data_in.version_owner = author_guid
        operation_body.version_owner = data_in.version_owner

    session.add(operation_body)
    await session.commit()

    for parameter_in in data_in.parameters:
        guid = str(uuid.uuid4())
        parameter = OperationBodyParameter(
            **parameter_in.dict(),
            guid=guid,
            operation_body_id=operation_body.operation_body_id
        )
        session.add(parameter)
        await session.commit()


async def create_operation(operation_in: OperationIn, session: AsyncSession, author_guid: str) -> Operation:
    guid = str(uuid.uuid4())

    if operation_in.owner is None:
        operation_in.owner = author_guid

    operation = Operation(
        **operation_in.dict(exclude={'tags', 'code', 'parameters'}),
        guid=guid
    )

    await add_tags(operation, operation_in.tags, session)
    session.add(operation)
    await session.commit()

    await create_operation_version(version=1, operation_id=operation.operation_id, data_in=operation_in, session=session)

    return operation


def need_create_version(operation_update_in: OperationUpdateIn) -> bool:
    return operation_update_in.code is not None or operation_update_in.parameters is not None


async def edit_operation(guid: str, operation_update_in: OperationUpdateIn, session: AsyncSession, author_guid: str):
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

    if need_create_version(operation_update_in=operation_update_in):
        operation_body = await session.execute(
            select(OperationBody)
            .options(selectinload(OperationBody.operation_body_parameters))
            .filter(OperationBody.operation_id == operation.operation_id)
            .order_by(OperationBody.version.desc())
        )
        operation_body = operation_body.scalars().first()
        await create_operation_version(version=operation_body.version+1, operation_id=operation.operation_id,
                                       data_in=operation_update_in, session=session, author_guid=author_guid)


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


async def check_on_operation_parameters_uniqueness(parameters: list[OperationParameterIn], session: AsyncSession,
                                                   guid: Optional[str] = None):
    list_parameters_in = []
    list_parameters_out = []
    for parameter in parameters:
        if parameter.flag:
            list_parameters_in.append(parameter.name)
        else:
            list_parameters_out.append(parameter.name)

    operation_body = await session.execute(
        select(OperationBody)
        .options(selectinload(OperationBody.operation_body_parameters))
        .filter(OperationBody.guid == guid)
    )
    operation_body = operation_body.scalars().first()
    if operation_body:
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
