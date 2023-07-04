from fastapi import APIRouter, Depends

from app.crud.crud_comment import create_comment, CommentOwnerTypes, verify_comment_owner, edit_comment, remove_comment
from app.crud.crud_pipeline import create_pipeline, read_all, read_by_guid, update_pipeline, delete_pipeline, \
    generate_pipeline
from app.dependencies import db_session, get_user, get_token
from app.schemas.comment import CommentIn
from app.schemas.pipeline import PipelineIn, PipelineUpdateIn

router = APIRouter(
    prefix="/pipelines",
    tags=['pipeline']
)


@router.post('/')
async def add_pipeline(pipeline_in: PipelineIn, session=Depends(db_session), user=Depends(get_user)):
    pipeline = await create_pipeline(pipeline_in=pipeline_in, session=session, author_guid=user['identity_id'])
    return {'guid': pipeline.guid}


@router.get('/')
async def read_pipelines(session=Depends(db_session), user=Depends(get_user)):
    return await read_all(session)


@router.get('/{guid}')
async def get_pipeline(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_by_guid(guid, token, session)


@router.put('/{guid}')
async def update(guid: str, pipeline_update_in: PipelineUpdateIn, session=Depends(db_session), user=Depends(get_user)):
    pipeline = await update_pipeline(guid, pipeline_update_in, session, user)
    return {'guid': pipeline.guid}


@router.delete('/{guid}')
async def delete(guid: str, session=Depends(db_session)):
    await delete_pipeline(guid, session)


@router.post('/{guid}/comments')
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, CommentOwnerTypes.pipeline, session)
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


@router.get('/generate/{pipeline_id}')
async def generate(pipeline_id: int, session=Depends(db_session), _=Depends(get_user)):
    await generate_pipeline(pipeline_id=pipeline_id, session=session)
