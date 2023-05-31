
from fastapi import APIRouter, Depends

from app.dependencies import db_session
from app.dependencies import get_user
from app.crud.crud_model_quality import read_all, read_by_id, delete_by_id

router = APIRouter(
    prefix="/model_qualities",
    tags=['model qualities']
)


@router.get('/')
async def get_all(session=Depends(db_session), user=Depends(get_user)):
    return await read_all(session)


@router.post('/')
async def create_model_quality(session=Depends(db_session), user=Depends(get_user)):
    return await read_all(session)


@router.get('/{id}')
async def get_model_quality(id: str, session=Depends(db_session), user=Depends(get_user)):
    return await read_by_id(id, session)


@router.delete('/{id}')
async def delete_model_quality(id: str, session=Depends(db_session), user=Depends(get_user)):
    await delete_by_id(id, session)