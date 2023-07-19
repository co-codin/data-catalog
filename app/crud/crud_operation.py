import uuid

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import Optional

from app.crud.crud_tag import add_tags, update_tags
from app.errors.errors import OperationNameAlreadyExist, OperationInputParametersNotExists
from app.models import AccessLabel
from app.models.models import Operation, OperationBody, OperationBodyParameter, ModelRelationOperation
from app.schemas.operation import OperationOut, OperationParameterIn, OperationIn, OperationManyOut, \
    OperationBodyOut, OperationBodyIn, ConfirmIn, OperationBodyUpdateIn, WarningOut, OperationBodyInfoOut


async def read_all(session: AsyncSession) -> list[OperationManyOut]:
    operations = await session.execute(
        select(Operation)
        .options(selectinload(Operation.tags))
        .order_by(Operation.created_at)
    )
    operations = operations.scalars().all()
    return [OperationManyOut.from_orm(operation) for operation in operations]


async def get_last_version(operation_id: int, session: AsyncSession):
    last_version = await session.execute(
        select(OperationBody)
        .filter(OperationBody.operation_id == operation_id)
        .order_by(OperationBody.version.desc())
    )
    return last_version.scalars().first()

async def read_by_guid(guid: str, session: AsyncSession) -> OperationOut:
    operation = await session.execute(
        select(Operation)
        .options(selectinload(Operation.tags))
        .filter(Operation.guid == guid)
    )

    operation = operation.scalars().first()
    if not operation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    operation_out = OperationOut.from_orm(operation)
    last_version = await get_last_version(operation.operation_id, session)
    operation_out.last_version = OperationBodyInfoOut(
        guid=last_version.guid,
        version=last_version.version
    )

    return operation_out


async def read_versions_list(guid: str, session: AsyncSession) -> [OperationBodyOut]:
    operation = await session.execute(
        select(Operation)
        .options(selectinload(Operation.tags))
        .filter(Operation.guid == guid)
    )
    operation = operation.scalars().first()
    if not operation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    operation_versions = await session.execute(
        select(OperationBody)
        .filter(OperationBody.operation_id == operation.operation_id)
    )
    operation_versions = operation_versions.scalars().all()
    return [OperationBodyOut.from_orm(operation_version) for operation_version in operation_versions]


async def create_parameter(body_id: int, data_in: OperationParameterIn, session: AsyncSession, flag: bool):
    parameter = OperationBodyParameter(
        guid=str(uuid.uuid4()),
        flag=flag,
        operation_body_id=body_id,
        **data_in.dict()
    )
    session.add(parameter)
    await session.commit()


async def create_operation_version(guid: str, operation_body_in: OperationBodyIn, session: AsyncSession, author_guid: str):
    if not len(operation_body_in.input):
        raise OperationInputParametersNotExists

    operation = await session.execute(
        select(Operation)
        .options(selectinload(Operation.tags))
        .filter(Operation.guid == guid)
    )
    operation = operation.scalars().first()
    if not operation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    last_version = await get_last_version(operation.operation_id, session)
    if last_version:
        version = last_version.version + 1
    else:
        version = 1

    if operation_body_in.owner is None:
        operation_body_in.owner = author_guid

    operation_body = OperationBody(
        **operation_body_in.dict(exclude={'tags', 'input', 'output', 'confirm'}),
        guid=str(uuid.uuid4()),
        operation_id=operation.operation_id,
        version=version
    )

    await add_tags(operation_body, operation_body_in.tags, session)
    session.add(operation_body)
    await session.commit()

    for parameter_in in operation_body_in.input:
        await create_parameter(operation_body.operation_body_id, parameter_in, session, True)

    await create_parameter(operation_body.operation_body_id, operation_body_in.output, session, False)


async def check_operation_version_in_use(id: int, session: AsyncSession):
    relation_count = await session.execute(
        select((func.count(ModelRelationOperation.id)))
        .filter(ModelRelationOperation.operation_body_id == id)
    )
    relation_count = relation_count.scalars().first()

    access_label_count = await session.execute(
        select(func.count(AccessLabel.id))
        .filter(AccessLabel.operation_version_id == id)
    )
    access_label_count = access_label_count.scalars().first()

    if relation_count or access_label_count:
        return WarningOut(
            in_relations=relation_count,
            in_attributes=access_label_count
        )

    return False


async def edit_operation_version(guid: str, operation_body_update_in: OperationBodyUpdateIn, session: AsyncSession, author_guid: str):
    operation_version = await session.execute(
        select(OperationBody)
        .options(selectinload(OperationBody.operation))
        .filter(OperationBody.guid == guid)
    )
    operation_version = operation_version.scalars().first()
    if not operation_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    check_in_use = await check_operation_version_in_use(operation_version.operation_body_id, session)

    if check_in_use:
        if operation_body_update_in.confirm:
            await create_operation_version(operation_version.operation.guid, operation_body_update_in, session, author_guid)
        else:
            return check_in_use
    else:
        operation_version_update_in_data = {
            key: value for key, value in operation_body_update_in.dict(exclude={'tags', 'confirm', 'input', 'output'}).items()
            if value is not None
        }

        await session.execute(
            update(OperationBody)
            .where(OperationBody.guid == guid)
            .values(
                **operation_version_update_in_data,
            )
        )

        operation_version = await session.execute(
            select(OperationBody)
            .options(selectinload(OperationBody.tags))
            .filter(OperationBody.guid == guid)
        )
        operation_version = operation_version.scalars().first()
        await update_tags(operation_version, session, operation_body_update_in.tags)

        await session.execute(
            delete(OperationBodyParameter)
            .where(OperationBodyParameter.operation_body_id == operation_version.operation_body_id)
        )

        for parameter_in in operation_body_update_in.input:
            await create_parameter(operation_version.operation_body_id, parameter_in, session, True)

        await create_parameter(operation_version.operation_body_id, operation_body_update_in.output, session, False)


async def delete_operation_version(guid: str, confirm_in: ConfirmIn, session: AsyncSession):
    if confirm_in.confirm == False:
        operation_version = await session.execute(
            select(OperationBody)
            .options(selectinload(OperationBody.operation))
            .filter(OperationBody.guid == guid)
        )
        operation_version = operation_version.scalars().first()
        if not operation_version:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        check_in_use = await check_operation_version_in_use(operation_version.operation_body_id, session)
        if check_in_use:
            return check_in_use

    await session.execute(
        delete(OperationBody)
        .where(OperationBody.guid == guid)
    )


async def create_operation(operation_in: OperationIn, session: AsyncSession, author_guid: str) -> Operation:
    guid = str(uuid.uuid4())

    if operation_in.owner is None:
        operation_in.owner = author_guid

    operation = Operation(
        **operation_in.dict(exclude={'tags'}),
        guid=guid
    )

    await add_tags(operation, operation_in.tags, session)
    session.add(operation)
    await session.commit()

    return operation


async def edit_operation(guid: str, operation_update_in: OperationIn, session: AsyncSession, author_guid: str):
    operation_update_in_data = {
        key: value for key, value in operation_update_in.dict(exclude={'tags'}).items()
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


async def delete_by_guid(guid: str, confirm_in: ConfirmIn, session: AsyncSession):
    if confirm_in.confirm == False:
        operation = await session.execute(
            select(Operation)
            .filter(Operation.guid == guid)
        )
        operation = operation.scalars().first()
        if not operation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        check_in_use = await check_operation_version_in_use(operation.operation_id, session)
        if check_in_use:
            return check_in_use

    await session.execute(
        delete(Operation)
        .where(Operation.guid == guid)
    )


async def check_on_operation_name_uniqueness(name: str, session: AsyncSession, guid: Optional[str] = None):
    operations = await session.execute(
        select(Operation)
        .where(Operation.name == name)
    )
    operations = operations.scalars().all()
    for operation in operations:
        if operation.name == name and operation.guid != guid:
            raise OperationNameAlreadyExist(name)
