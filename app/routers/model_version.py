
from app.crud.crud_model_version import create_model_version, read_by_id, confirm_model_version
from app.crud.crud_source_registry import remove_redundant_tags
from app.dependencies import db_session

from fastapi import APIRouter, Depends, HTTPException
from app.models.model import ModelVersion

from app.schemas.model_version import ModelVersionIn

router = APIRouter(
    prefix="/model_versions",
    tags=['model versions']
)

@router.get('/{id}')
async def get_model_version(id: str, session=Depends(db_session)):
    return await read_by_id(id, session)


@router.post('/')
async def add_model_version(model_version_in: ModelVersionIn, session=Depends(db_session)):
    id = await create_model_version(model_version_in, session)

    return {'id': id}


@router.put('/{id}/confirm')
async def confirm(id: str, session=Depends(db_session)):
    return await confirm_model_version(id, session)