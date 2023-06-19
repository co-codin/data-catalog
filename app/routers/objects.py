from typing import Dict, List

from fastapi import APIRouter, Depends


from app.crud.crud_object import (
    create_object, read_all, read_by_guid, edit_object, edit_is_synchronizing, select_object_fields, read_object_by_guid
)
from app.crud.crud_comment import create_comment, verify_comment_owner, edit_comment, remove_comment, CommentOwnerTypes
from app.crud.crud_tag import remove_redundant_tags

from app.dependencies import db_session, get_user, get_token

from app.schemas.objects import ObjectIn, ObjectManyOut, ObjectOut, ObjectUpdateIn, FieldManyOut
from app.schemas.source_registry import CommentIn
from app.schemas.migration import MigrationPattern

from app.services.synchronizer import send_for_synchronization


router = APIRouter(
    prefix='/objects',
    tags=['object']
)


@router.post('/')
async def add_object(
        object_in: ObjectIn, migration_pattern: MigrationPattern, session=Depends(db_session), _=Depends(get_user)
):
    object_to_synch = await create_object(object_in, session)
    await send_for_synchronization(**object_to_synch.dict(), migration_pattern=migration_pattern)
    return {'guid': object_to_synch.object_guid}


@router.post('/{guid}/synchronize')
async def synchronize(guid: str, migration_pattern: MigrationPattern, session=Depends(db_session), _=Depends(get_user)):
    object_synch = await read_object_by_guid(guid, session)
    await send_for_synchronization(**object_synch.dict(), migration_pattern=migration_pattern)
    return {'msg': 'object has been sent to synchronize'}


@router.get('/', response_model=List[ObjectManyOut])
async def get_all(session=Depends(db_session), _=Depends(get_user)):
    return await read_all(session)


@router.get('/{guid}', response_model=ObjectOut)
async def get_by_guid(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_by_guid(guid, token, session)


@router.put('/{guid}', response_model=Dict[str, str])
async def update_object(
        guid: str, object_update_in: ObjectUpdateIn, session=Depends(db_session), _=Depends(get_user)
):
    await edit_object(guid, object_update_in, session)
    await remove_redundant_tags(session)
    return {'msg': 'object has been updated'}


@router.put('/{guid}/')
async def set_is_synchronizing(guid: str, is_synchronizing: bool, session=Depends(db_session), _=Depends(get_user)):
    await edit_is_synchronizing(guid, is_synchronizing, session)
    return {'msg': 'is_synchronized field has been set'}


@router.post('/{guid}/comments', response_model=Dict[str, int])
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, CommentOwnerTypes.object_, session)
    return {'id': comment_id}


@router.put('/comments/{id_}', response_model=Dict[str, str])
async def update_comment(id_: int, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    await verify_comment_owner(id_, user['identity_id'], session)
    await edit_comment(id_, comment, session)
    return {'msg': 'comment has been updated'}


@router.delete('/comments/{id_}', response_model=Dict[str, str])
async def delete_comment(id_: int, session=Depends(db_session), user=Depends(get_user)):
    await verify_comment_owner(id_, user['identity_id'], session)
    await remove_comment(id_, session)
    return {'msg': 'comment has been deleted'}


@router.get('/{guid}/fields', response_model=list[FieldManyOut])
async def get_object_fields(guid: str, session=Depends(db_session), _=Depends(get_user)):
    return await select_object_fields(guid, session)
