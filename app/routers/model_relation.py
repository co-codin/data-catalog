from fastapi import APIRouter, Depends

from app.dependencies import db_session, get_user, get_token
from app.crud.crud_model_relation import read_relations_by_version, read_relation_by_guid, create_model_relation, \
    update_model_relation, delete_model_relation
from app.schemas.model_relation import ModelRelationIn, ModelRelationUpdateIn

router = APIRouter(
    prefix="/model_relations",
    tags=['model relations']
)


@router.get('/by_version/{version_id}')
async def read_model_relations(version_id: int, session=Depends(db_session), _=Depends(get_user)):
    return await read_relations_by_version(version_id, session)


@router.get('/{guid}')
async def get_model_relation(guid: str, session=Depends(db_session), _=Depends(get_token)):
    return await read_relation_by_guid(guid, session)


@router.post('/')
async def add_model_relation(relation_in: ModelRelationIn, session=Depends(db_session), _=Depends(get_user)):
    guid = await create_model_relation(relation_in, session)

    return {'guid': guid}


@router.put('/{guid}')
async def update(guid: str, relation_update_in: ModelRelationUpdateIn, session=Depends(db_session),
                 _=Depends(get_user)):
    return await update_model_relation(guid, relation_update_in, session)


@router.delete('/{guid}')
async def delete(guid: str, session=Depends(db_session), _=Depends(get_user)):
    await delete_model_relation(guid, session)
