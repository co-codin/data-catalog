from fastapi import APIRouter, Depends
from app.dependencies import db_session, get_user, get_token
from app.crud.crud_model_resource import read_resources_by_version_id, read_resources_by_guid, create_model_resource, \
    update_model_resource, delete_model_resource
from app.crud.crud_comment import CommentOwnerTypes, create_comment, edit_comment, remove_comment, verify_comment_owner
from app.schemas.model_resource import ModelResourceIn, ModelResourceUpdateIn
from app.schemas.source_registry import CommentIn

router = APIRouter(
    prefix="/model_resource",
    tags=['model resource']
)


@router.get('/by_version/{version_id}')
async def get_model_resources(version_id: int, session=Depends(db_session), user=Depends(get_user)):
    return await read_resources_by_version_id(version_id, session)


@router.get('/{guid}')
async def get_model_resource(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_resources_by_guid(guid, token, session)


@router.post('/')
async def add_model_resource(resource_in: ModelResourceIn, session=Depends(db_session), user=Depends(get_user)):
    guid = await create_model_resource(resource_in, session)

    return {'guid': guid}


@router.put('/{guid}')
async def update(guid: str, resource_update_in: ModelResourceUpdateIn, session=Depends(db_session),
                 user=Depends(get_user)):
    return await update_model_resource(guid, resource_update_in, session)


@router.delete('/{guid}')
async def delete(guid: str, session=Depends(db_session), user=Depends(get_user)):
    return await delete_model_resource(guid, session)


@router.post('/{guid}/comments')
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, CommentOwnerTypes.model_resource, session)
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