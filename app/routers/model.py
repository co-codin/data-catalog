
from app.crud.crud_model import check_on_model_uniqueness, create_model, read_all, read_by_guid
from app.dependencies import db_session
from typing import List, Dict

from fastapi import APIRouter, Depends
from app.models.model import Model

from app.schemas.model import ModelIn

router = APIRouter(
    prefix="/models",
    tags=['model']
)

@router.get('/')
async def read_models(session=Depends(db_session)):
    return await read_all(session)



@router.post('/')
async def add_model(model_in: ModelIn, session=Depends(db_session)):
    await check_on_model_uniqueness(name=model_in.name, session=session)
    await create_model(model_in, session)



@router.get('/{guid}')
async def get_model(guid: str, session=Depends(db_session)):
    return await read_by_guid(session, guid)


@router.delete('/{guid}')
async def create_model(session=Depends(db_session)):
    pass