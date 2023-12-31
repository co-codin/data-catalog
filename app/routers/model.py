import asyncio

from fastapi import APIRouter, Depends

from app.crud.crud_comment import CommentOwnerTypes, create_comment, edit_comment, remove_comment, verify_comment_owner
from app.crud.crud_tag import remove_redundant_tags
from app.crud.crud_model import (
    check_on_model_uniqueness, create_model, delete_by_guid, edit_model, read_all, read_by_guid, get_models_by_operation
)

from app.dependencies import db_session, get_token, get_user

from app.schemas.model import ModelIn, ModelUpdateIn
from app.schemas.source_registry import CommentIn

router = APIRouter(
    prefix="/models",
    tags=['model']
)


@router.get('/')
async def read_models(session=Depends(db_session), _=Depends(get_user)):
    return await read_all(session)


@router.get('/{guid}')
async def get_model(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_by_guid(guid, token, session)


@router.put('/{guid}')
async def update_model(guid: str, model_in: ModelUpdateIn, session=Depends(db_session), _=Depends(get_user)):
    await check_on_model_uniqueness(name=model_in.name, session=session, guid=guid)
    await edit_model(guid, model_in, session)
    asyncio.create_task(remove_redundant_tags())


@router.post('/')
async def add_model(model_in: ModelIn, session=Depends(db_session), _=Depends(get_user)):
    await check_on_model_uniqueness(name=model_in.name, session=session)
    model = await create_model(model_in, session)
    return {'guid': model.guid}


@router.delete('/{guid}')
async def delete_model(guid: str, session=Depends(db_session), user=Depends(get_user)):
    await delete_by_guid(guid=guid, session=session, identity_id=user['identity_id'])


@router.post('/{guid}/comments')
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, CommentOwnerTypes.model, session)
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


@router.get('/operation/{guid}')
async def read_models_by_operaion(guid: str, session=Depends(db_session), _=Depends(get_user)):
    return await get_models_by_operation(guid, session)
