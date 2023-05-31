
from fastapi import APIRouter, Depends

from app.dependencies import db_session, get_user
from app.crud.crud_model_quality import read_all, create, update_by_id, read_by_id, delete_by_id
from app.schemas.model_quality import ModelQualityIn, ModelQualityUpdateIn

router = APIRouter(
    prefix="/model_qualities",
    tags=['model qualities']
)


@router.get('/')
async def get_all(session=Depends(db_session), user=Depends(get_user)):
    return await read_all(session)


@router.post('/')
async def create_model_quality(model_quality_in: ModelQualityIn, session=Depends(db_session), user=Depends(get_user)):
    guid = await create(model_quality_in, session)
    return {'guid': guid}


@router.put('/{id}')
async def update_model_quality(id: str, model_quality_update_in: ModelQualityUpdateIn, session=Depends(db_session), user=Depends(get_user)):
    return await update_by_id(id, model_quality_update_in, session)


@router.get('/{id}')
async def get_model_quality(id: str, session=Depends(db_session), user=Depends(get_user)):
    return await read_by_id(id, session)


@router.delete('/{id}')
async def delete_model_quality(id: str, session=Depends(db_session), user=Depends(get_user)):
    await delete_by_id(id, session)