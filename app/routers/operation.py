from fastapi import APIRouter, Depends

from app.crud.crud_operation import read_all, read_by_guid, check_on_operation_name_uniqueness, \
    create_operation, edit_operation, delete_by_guid, read_versions_list, create_operation_version, \
    edit_operation_version, delete_operation_version
from app.dependencies import db_session, get_user
from app.schemas.operation import OperationIn, OperationBodyIn, OperationBodyUpdateIn, ConfirmIn

router = APIRouter(
    prefix="/operation",
    tags=['operation']
)


@router.post('/')
async def add_operation(operation_in: OperationIn, session=Depends(db_session), user=Depends(get_user)):
    await check_on_operation_name_uniqueness(name=operation_in.name, session=session)
    operation = await create_operation(operation_in=operation_in, session=session, author_guid=user['identity_id'])
    return {'guid': operation.guid}


@router.get('/')
async def read_operations(session=Depends(db_session), _=Depends(get_user)):
    return await read_all(session)


@router.get('/{guid}')
async def get_operation(guid: str, session=Depends(db_session), _=Depends(get_user)):
    return await read_by_guid(guid, session)


@router.get('/{guid}/version')
async def get_operation_versions(guid: str, session=Depends(db_session), _=Depends(get_user)):
    return await read_versions_list(guid, session)


@router.post('/{guid}/version')
async def add_operation_version(guid: str, operation_body_in: OperationBodyIn, session=Depends(db_session),
                                user=Depends(get_user)):
    return await create_operation_version(guid, operation_body_in, session, author_guid=user['identity_id'])


@router.put('/version/{guid}')
async def update_operation_version(guid: str, operation_body_update_in: OperationBodyUpdateIn,
                                   session=Depends(db_session), user=Depends(get_user)):
    return await edit_operation_version(guid, operation_body_update_in, session, author_guid=user['identity_id'])


@router.delete('/version/{guid}')
async def remove_operation_version(guid: str, confirm_in: ConfirmIn, session=Depends(db_session), _=Depends(get_user)):
    return await delete_operation_version(guid, confirm_in, session)


@router.put('/{guid}')
async def update_operation(guid: str, operation_update_in: OperationIn, session=Depends(db_session),
                           user=Depends(get_user)):
    await edit_operation(guid, operation_update_in, session, author_guid=user['identity_id'])


@router.delete('/{guid}')
async def delete_operation(guid: str, confirm_in: ConfirmIn, session=Depends(db_session), _=Depends(get_user)):
    return await delete_by_guid(guid, confirm_in, session)
