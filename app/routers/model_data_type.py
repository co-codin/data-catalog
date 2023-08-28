from fastapi import APIRouter, Depends

from app.dependencies import db_session, get_user
from app.crud.crud_model_data_type import read_all, read_by_id

router = APIRouter(
    prefix="/model_data_types",
    tags=['model data types']
)


@router.get('/')
async def get_all(session=Depends(db_session), _=Depends(get_user)):
    return await read_all(session)


@router.get('/{id}')
async def get_model_data_type(id: int, session=Depends(db_session), _=Depends(get_user)):
    return await read_by_id(id, session)
