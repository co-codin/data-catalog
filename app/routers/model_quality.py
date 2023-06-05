
from fastapi import APIRouter, Depends

from app.dependencies import db_session, get_user
from app.crud.crud_model_quality import read_all, create, update_by_guid, read_by_guid, delete_by_guid
from app.schemas.model_quality import ModelQualityIn, ModelQualityUpdateIn

router = APIRouter(
    prefix="/model_qualities",
    tags=['model qualities']
)


@router.get('/{model_version_id}')
async def get_all(model_version_id: str, session=Depends(db_session), user=Depends(get_user)):
    return await read_all(model_version_id, session)


@router.post('/')
async def create_model_quality(model_quality_in: ModelQualityIn, session=Depends(db_session), user=Depends(get_user)):
    guid = await create(model_quality_in, session)
    return {'guid': guid}


@router.put('/{guid}')
async def update_model_quality(guid: int, model_quality_update_in: ModelQualityUpdateIn, session=Depends(db_session), user=Depends(get_user)):
    return await update_by_guid(guid, model_quality_update_in, session)


@router.get('/{guid}')
async def get_model_quality(guid: str, session=Depends(db_session), user=Depends(get_user)):
    return await read_by_guid(guid, session)


@router.delete('/{guid}')
async def delete_model_quality(guid: str, session=Depends(db_session), user=Depends(get_user)):
    await delete_by_guid(guid, session)