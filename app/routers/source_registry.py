from typing import List, Dict

from fastapi import APIRouter, Depends

from app.crud.crud_source_registry import (
    create_source_registry, read_all, read_by_guid, edit_source_registry, remove_source_registry,
    create_comment, edit_comment, remove_comment, verify_comment_owner,
    create_tag, remove_tag
)
from app.schemas.source_registry import SourceRegistryIn, SourceRegistryUpdateIn, SourceRegistryOut, CommentIn
from app.dependencies import db_session, get_user, get_token

router = APIRouter(
    tags=['source registry']
)


@router.post('/', response_model=Dict[str, str])
async def add_source_registry(source_registry: SourceRegistryIn, session=Depends(db_session), user=Depends(get_user)):
    guid = await create_source_registry(source_registry, user['identity_id'], session)
    return {'guid': guid}


@router.put('/{guid}', response_model=Dict[str, str])
async def update_source_registry(
        guid: str, source_registry: SourceRegistryUpdateIn, session=Depends(db_session), _=Depends(get_user)
):
    await edit_source_registry(guid, source_registry, session)
    return {'msg': 'source registry has been updated'}


@router.delete('/{guid}', response_model=Dict[str, str])
async def delete_source_registry(guid: str, session=Depends(db_session), _=Depends(get_user)):
    await remove_source_registry(guid, session)
    return {'msg': 'source registry has been deleted'}


@router.get('/', response_model=List[SourceRegistryOut])
async def get_all(session=Depends(db_session), token=Depends(get_token)) -> List[SourceRegistryOut]:
    return await read_all(token, session)


@router.get('/{guid}', response_model=SourceRegistryOut)
async def get_by_guid(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_by_guid(guid, token, session)


@router.post('/{guid}/comments', response_model=Dict[str, int])
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, session)
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


@router.post('/{guid}/tags', response_model=Dict[str, int])
async def add_tag(guid: str, tag: str, session=Depends(db_session), _=Depends(get_user)):
    tag_id = await create_tag(guid, tag, session)
    return {'id': tag_id}


@router.delete('/tags/{id_}', response_model=Dict[str, str])
async def delete_tag(id_: int, session=Depends(db_session), _=Depends(get_user)):
    await remove_tag(id_, session)
    return {'msg': 'tag has been deleted'}
