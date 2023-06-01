from fastapi import APIRouter, Depends

from app.crud.crud_comment import CommentOwnerTypes, verify_comment_owner, edit_comment, remove_comment, create_comment
from app.schemas.objects import FieldOut, FieldUpdateIn
from app.crud.crud_field import select_field, alter_field
from app.dependencies import db_session, get_token, get_user
from app.schemas.source_registry import CommentIn

router = APIRouter(
    prefix='/fields',
    tags=['field']
)


@router.get('/{field_guid}', response_model=FieldOut)
async def get_field(field_guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await select_field(field_guid, token, session)


@router.put('/{field_guid}', response_model=dict[str, str])
async def update_field(
        field_guid: str, field_update_in: FieldUpdateIn, session=Depends(db_session), _=Depends(get_user)
):
    await alter_field(field_guid, field_update_in, session)
    return {'msg': f'field with guid {field_guid} has been updated'}


@router.post('/{guid}/comments', response_model=dict[str, int])
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, CommentOwnerTypes.field, session)
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
