from fastapi import APIRouter, Depends

from app.crud.crud_operation import read_all, read_by_guid, check_on_operation_name_uniqueness, \
    check_on_operation_parameters_uniqueness, create_operation, edit_operation, delete_by_guid
from app.dependencies import db_session, get_user
from app.schemas.operation import OperationIn, OperationUpdateIn

router = APIRouter(
    prefix="/operation",
    tags=['operation']
)


@router.post('/')
async def add_model(operation_in: OperationIn, session=Depends(db_session), _=Depends(get_user)):
    await check_on_operation_name_uniqueness(name=operation_in.name, session=session)
    await check_on_operation_parameters_uniqueness(parameters=operation_in.parameters, session=session)
    operation = await create_operation(operation_in=operation_in, session=session)
    return {'guid': operation.guid}


@router.get('/')
async def read_operations(session=Depends(db_session), _=Depends(get_user)):
    return await read_all(session)


@router.get('/{guid}')
async def get_model(guid: str, session=Depends(db_session), _=Depends(get_user)):
    return await read_by_guid(guid, session)


@router.put('/{guid}')
async def update_operation(guid: str, operation_update_in: OperationUpdateIn, session=Depends(db_session),
                           _=Depends(get_user)):
    await check_on_operation_name_uniqueness(name=operation_update_in.name, session=session, guid=guid)
    await check_on_operation_parameters_uniqueness(parameters=operation_update_in.parameters, session=session,
                                                   guid=guid)
    await edit_operation(guid, operation_update_in, session)


@router.delete('/{guid}')
async def delete_operation(guid: str, session=Depends(db_session), _=Depends(get_user)):
    await delete_by_guid(guid, session)
