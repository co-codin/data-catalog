
from app.crud.crud_comment import CommentOwnerTypes, create_comment, edit_comment, remove_comment, verify_comment_owner
from app.crud.crud_model_version import create_model_version, read_by_id, confirm_model_version
from app.crud.crud_source_registry import remove_redundant_tags
from app.dependencies import db_session, get_user

from fastapi import APIRouter, Depends, HTTPException
from app.models.model import ModelVersion

from app.schemas.model_version import ModelVersionIn
from app.schemas.source_registry import CommentIn

router = APIRouter(
    prefix="/model_versions",
    tags=['model versions']
)

@router.get('/{id}')
async def get_model_version(id: str, session=Depends(db_session)):
    return await read_by_id(id, session)


@router.post('/')
async def add_model_version(model_version_in: ModelVersionIn, session=Depends(db_session)):
    id = await create_model_version(model_version_in, session)

    return {'id': id}


@router.put('/{id}/confirm')
async def confirm(id: str, session=Depends(db_session)):
    return await confirm_model_version(id, session)



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