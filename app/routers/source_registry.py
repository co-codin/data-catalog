import asyncio

from fastapi import APIRouter, Depends, Body

from app.crud.crud_source_registry import (
    check_on_uniqueness, create_source_registry, read_all, read_by_guid, edit_source_registry,
    set_source_registry_status, read_names_by_status, get_objects, read_source_registry_by_guid
)
from app.crud.crud_tag import remove_redundant_tags
from app.crud.crud_comment import create_comment, edit_comment, remove_comment, verify_comment_owner, CommentOwnerTypes
from app.enums.enums import SyncType
from app.models import Status

from app.schemas.migration import MigrationPattern
from app.schemas.model import ModelCommon
from app.schemas.source_registry import (
    SourceRegistryIn, SourceRegistryOut, CommentIn, SourceRegistryManyOut
)

from app.dependencies import db_session, get_user, get_token

from app.services.synchronizer import send_for_synchronization

router = APIRouter(
    prefix="/source_registries",
    tags=['source registry']
)


@router.post('/', response_model=dict[str, str])
async def add_source_registry(
        source_registry: SourceRegistryIn, migration_pattern: MigrationPattern,
        model_in: ModelCommon = Body(None), session=Depends(db_session), user=Depends(get_user)
):
    await check_on_uniqueness(name=source_registry.name, conn_string=source_registry.conn_string, session=session)
    source_registry_model = await create_source_registry(source_registry, session)
    await send_for_synchronization(
        source_guid=source_registry_model.guid, conn_string=source_registry.conn_string,
        migration_pattern=migration_pattern, model_in=model_in, identity_id=user['identity_id'],
        sync_type=SyncType.ADD_SOURCE.value, source_name=source_registry_model.name
    )
    return {'guid': source_registry_model.guid}


@router.post('/{guid}/synchronize')
async def synchronize(
        guid: str, migration_pattern: MigrationPattern, session=Depends(db_session),
        user=Depends(get_user)
):
    source_registry_synch = await read_source_registry_by_guid(guid, session)
    await send_for_synchronization(
        **source_registry_synch.dict(), migration_pattern=migration_pattern,
        identity_id=user['identity_id'], sync_type=SyncType.SYNC_SOURCE.value
    )


@router.put('/{guid}', response_model=dict[str, str])
async def update_source_registry(
        guid: str, source_registry: SourceRegistryIn, session=Depends(db_session), _=Depends(get_user)
):
    await check_on_uniqueness(
        guid=guid, name=source_registry.name, conn_string=source_registry.conn_string, session=session
    )
    await edit_source_registry(guid, source_registry, session)
    asyncio.create_task(remove_redundant_tags())
    return {'msg': 'source registry has been updated'}


@router.post('/{guid}/status')
async def set_status(guid: str, status_in: Status, session=Depends(db_session), _=Depends(get_user)):
    await set_source_registry_status(guid, status_in, session)
    return {'msg': 'status has been set'}


@router.get('/', response_model=list[SourceRegistryManyOut])
async def get_all(session=Depends(db_session), _=Depends(get_user)) -> list[SourceRegistryManyOut]:
    return await read_all(session)


@router.get('/filter')
async def get_names_by_status(status: Status, session=Depends(db_session), _=Depends(get_user)):
    """
    Get all source registries with a given status: on, off, synchronizing
    return {guid: source_registry_guid, name: source_registry_name}
    """
    return await read_names_by_status(status, session)


@router.get('/{guid}', response_model=SourceRegistryOut)
async def get_by_guid(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_by_guid(guid, token, session)


@router.post('/{guid}/comments', response_model=dict[str, int])
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, CommentOwnerTypes.source_registry, session)
    return {'id': comment_id}


@router.put('/comments/{id_}', response_model=dict[str, str])
async def update_comment(id_: int, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    await verify_comment_owner(id_, user['identity_id'], session)
    await edit_comment(id_, comment, session)
    return {'msg': 'comment has been updated'}


@router.delete('/comments/{id_}', response_model=dict[str, str])
async def delete_comment(id_: int, session=Depends(db_session), user=Depends(get_user)):
    await verify_comment_owner(id_, user['identity_id'], session)
    await remove_comment(id_, session)
    return {'msg': 'comment has been deleted'}


@router.get('/{guid}/objects')
async def read_objects(guid: str, session=Depends(db_session), _=Depends(get_user)) -> set[str]:
    """
    Read objects of the given source registry(guid) which are not present in the data catalog
    return List[str] - list of object names

    1) Read all table names from the database which is referenced by the conn_string field
    2) Read all object names in the local database which belong to the source registry
    3) Calculate the set difference = source_objects_sets - local_objects_set
    4) Return the difference
    """
    return await get_objects(guid, session)
