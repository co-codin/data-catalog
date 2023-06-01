from fastapi import APIRouter, Depends

from app.dependencies import db_session, get_user, get_token
from app.crud.crud_model_relation_group import read_relation_groups, read_relation_group_by_guid, create_model_relation_group, update_model_relation_group, delete_model_relation_group
from app.schemas.model_relation_group import ModelRelationGroupIn, ModelRelationGroupUpdateIn

router = APIRouter(
    prefix="/model_relation_groups",
    tags=['model relation groups']
)


@router.get('/')
async def read_model_relation_groups(session=Depends(db_session), user=Depends(get_user)):
    return await read_relation_groups(session)


@router.get('/{guid}')
async def get_model_relation_group(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_relation_group_by_guid(guid, token, session)


@router.post('/')
async def add_model_relation_group(relation_group_in: ModelRelationGroupIn, session=Depends(db_session), user=Depends(get_user)):
    guid = await create_model_relation_group(relation_group_in, session)

    return {'guid': guid}


@router.put('/{guid}')
async def update(guid: str, relation_group_update_in: ModelRelationGroupUpdateIn, session=Depends(db_session), user=Depends(get_user)):
    return await update_model_relation_group(guid, relation_group_update_in, session)


@router.delete('/{guid}')
async def delete(guid: str, session=Depends(db_session), user=Depends(get_user)):
    await delete_model_relation_group(guid, session)