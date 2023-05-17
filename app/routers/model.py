
from neo4j import AsyncSession
from app.crud.crud_model import check_on_model_uniqueness, create_model
from app.dependencies import db_session, get_user, get_token
from typing import List, Dict, Set

from fastapi import APIRouter, Depends
from app.models.model import Model

from app.schemas.model import ModelIn

router = APIRouter(
    prefix="/models",
    tags=['model']
)

@router.post('/', response_model=Dict[str, str])
async def add_model(model_in: ModelIn, session=Depends(db_session), _=Depends(get_user)):
    await check_on_model_uniqueness(name=model_in.name, session=session)
    await create_model(model_in, session)


@router.get('/', response_model=List[Model])
async def read_all():
    pass
