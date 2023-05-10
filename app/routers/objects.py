from typing import Dict

from fastapi import APIRouter, Depends


from app.crud.crud_object import create_object
from app.crud.crud_comment import create_comment, verify_comment_owner, edit_comment, remove_comment, CommentOwnerTypes
from app.schemas.objects import ObjectIn
from app.dependencies import db_session, get_user
from app.schemas.source_registry import CommentIn

router = APIRouter(
    prefix='/objects',
    tags=['object']
)


@router.post('/')
async def add_object(object_in: ObjectIn, session=Depends(db_session), _=Depends(get_user)):
    guid = await create_object(object_in, session)
    return {'guid': guid}


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
