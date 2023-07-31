from fastapi import APIRouter, Depends

from app.dependencies import db_session, get_user, get_token
from app.crud.crud_model_quality import (
    create, update_by_guid, read_by_guid, delete_by_guid, check_on_model_quality_uniqueness
)
from app.crud.crud_comment import CommentOwnerTypes, create_comment, edit_comment, remove_comment, verify_comment_owner
from app.schemas.model_quality import ModelQualityIn, ModelQualityUpdateIn
from app.schemas.source_registry import CommentIn

router = APIRouter(
    prefix="/model_qualities",
    tags=['model qualities']
)

@router.post('/')
async def create_model_quality(model_quality_in: ModelQualityIn, session=Depends(db_session), _=Depends(get_user)):
    await check_on_model_quality_uniqueness(
        model_quality_in.name, session, model_version_id=model_quality_in.model_version_id
    )
    guid = await create(model_quality_in, session)
    return {'guid': guid}


@router.put('/{guid}')
async def update_model_quality(
        guid: str, model_quality_update_in: ModelQualityUpdateIn, session=Depends(db_session), _=Depends(get_user)
):
    await check_on_model_quality_uniqueness(model_quality_update_in.name, session, guid=guid)
    return await update_by_guid(guid, model_quality_update_in, session)


@router.get('/{guid}')
async def get_model_quality(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_by_guid(guid, token, session)


@router.delete('/{guid}')
async def delete_model_quality(guid: str, session=Depends(db_session), user=Depends(get_user)):
    await delete_by_guid(guid, session)


@router.post('/{guid}/comments')
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, CommentOwnerTypes.model_quality, session)
    return {'id': comment_id}


@router.put('/comments/{id_}')
async def update_comment(id_: int, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    await verify_comment_owner(id_, user['identity_id'], session)
    await edit_comment(id_, comment, session)
    return {'msg': 'comment has been updated'}


@router.delete('/comments/{id_}')
async def delete_comment(id_: int, session=Depends(db_session), user=Depends(get_user)):
    await verify_comment_owner(id_, user['identity_id'], session)
    await remove_comment(id_, session)
    return {'msg': 'comment has been deleted'}