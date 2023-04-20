from typing import List

from fastapi import APIRouter, Depends

from app.crud.crud_source_registry import (
    create_source_registry, read_all, read_by_guid, edit_source_registry, remove_source_registry,
    create_comment, edit_comment, remove_comment,
    create_tag, remove_tag
)
from app.schemas.source_registry import SourceRegistryIn, SourceRegistryUpdateIn, SourceRegistryOut, CommentIn
from app.dependencies import db_session, get_user

router = APIRouter(
    tags=['source registry']
)


@router.post('/')
async def add_source_registry(source_registry: SourceRegistryIn, session=Depends(db_session), user=Depends(get_user)):
    guid = await create_source_registry(source_registry, session)
    return {'guid': guid}


@router.put('/{guid}')
async def update_source_registry(
        guid: str, source_registry: SourceRegistryUpdateIn, session=Depends(db_session), user=Depends(get_user)
):
    await edit_source_registry(guid, source_registry, session)
    return {'msg': 'source registry has been updated'}


@router.delete('/{guid}')
async def delete_source_registry(guid: str, session=Depends(db_session), user=Depends(get_user)):
    await remove_source_registry(guid, session)
    return {'msg': 'source registry has been deleted'}


@router.get('/', response_model=List[SourceRegistryOut])
async def get_all(session=Depends(db_session), user=Depends(get_user)) -> List[SourceRegistryOut]:
    return await read_all(session)


@router.get('/{guid}', response_model=SourceRegistryOut)
async def get_by_guid(guid: str, session=Depends(db_session), user=Depends(get_user)):
    return await read_by_guid(guid, session)


@router.post('/{guid}/comment')
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user.guid, comment, session)
    return {'id': comment_id}


@router.put('/comment/{id_}')
async def update_comment(id_: int, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    await edit_comment(id_, user.guid, comment, session)
    return {'msg': 'comment has been updated'}


@router.delete('/comment/{id_}')
async def delete_comment(id_: int, session=Depends(db_session), user=Depends(get_user)):
    await remove_comment(id_, user.guid, session)
    return {'msg': 'comment has been deleted'}


@router.post('/{guid}/tag')
async def add_tag(guid: str, tag: str, session=Depends(db_session), user=Depends(get_user)):
    tag_id = await create_tag(guid, tag, session)
    return {'id': tag_id}


@router.post('/tag/{id_}')
async def delete_tag(id_: int, session=Depends(db_session), user=Depends(get_user)):
    await remove_tag(id_, session)
    return {'msg': 'tag has been deleted'}
