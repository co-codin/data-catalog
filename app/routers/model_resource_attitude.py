from fastapi import APIRouter, Depends
from app.dependencies import db_session, get_user, get_token
from app.crud.crud_model_attitude import read_attitudes_by_resource_id, create_model_attitude, delete_model_attitude
from app.schemas.model_attitude import ModelAttitudeIn

router = APIRouter(
    prefix="/model_attitude",
    tags=['model attitude']
)


@router.get('/by_resource/{resource_id}')
async def get_model_attitudes(resource_id: int, session=Depends(db_session), user=Depends(get_user)):
    return await read_attitudes_by_resource_id(resource_id, session)


@router.post('/')
async def add_model_attitude(attitude_in: ModelAttitudeIn, session=Depends(db_session), user=Depends(get_user)):
    guid = await create_model_attitude(attitude_in, session)

    return {'guid': guid}


@router.delete('/{guid}')
async def delete(guid: str, session=Depends(db_session), user=Depends(get_user)):
    return await delete_model_attitude(guid, session)
