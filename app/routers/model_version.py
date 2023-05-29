
from app.crud.crud_comment import CommentOwnerTypes, create_comment, edit_comment, remove_comment, verify_comment_owner
from app.crud.crud_model_version import create_model_version, delete_model_version, read_by_guid, update_model_version
from app.dependencies import db_session, get_token, get_user

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.model_version import ModelVersionIn, ModelVersionUpdateIn
from app.schemas.source_registry import CommentIn

router = APIRouter(
    prefix="/model_versions",
    tags=['model versions']
)

@router.get('/{guid}')
async def get_model_version(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_by_guid(guid, token, session)


@router.post('/')
async def add_model_version(model_version_in: ModelVersionIn, session=Depends(db_session), user=Depends(get_user)):
    guid = await create_model_version(model_version_in, session)

    return {'guid': guid}


@router.put('/{guid}')
async def update(guid: str, model_version_update_in: ModelVersionUpdateIn, session=Depends(db_session), user=Depends(get_user)):
    return await update_model_version(guid, model_version_update_in, session)


@router.delete('/{guid}')
async def delete(guid: str, session=Depends(db_session)):
    try:
        await delete_model_version(guid, session)
    except:
        raise HTTPException(status_code=403, detail='Можно удалить только черновика')


@router.post('/{guid}/comments')
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, CommentOwnerTypes.model_version, session)
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