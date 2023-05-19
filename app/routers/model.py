
from app.crud.crud_model import check_on_model_uniqueness, create_model, delete_by_guid, edit_model, read_all, read_by_guid
from app.crud.crud_source_registry import remove_redundant_tags
from app.dependencies import db_session

from fastapi import APIRouter, Depends, HTTPException
from app.models.model import Model

from app.schemas.model import ModelIn

router = APIRouter(
    prefix="/models",
    tags=['model']
)

@router.get('/')
async def read_models(session=Depends(db_session)):
    return await read_all(session)


@router.get('/{guid}')
async def get_model(guid: str, session=Depends(db_session)):
    return await read_by_guid(guid, session)


@router.put('/{guid}')
async def update_model(guid: str, model_in: ModelIn, session=Depends(db_session)):
    await check_on_model_uniqueness(
        guid=guid, name=model_in.name, session=session
    )
    await edit_model(guid, model_in, session)
    await remove_redundant_tags(session)



@router.post('/')
async def add_model(model_in: ModelIn, session=Depends(db_session)):
    try:
        await check_on_model_uniqueness(name=model_in.name, session=session)
        guid = await create_model(model_in, session)
        return {'guid': guid}
    except:
        raise HTTPException(status_code=400, detail="Модель уже существует")




@router.delete('/{guid}')
async def delete_model(guid: str, session=Depends(db_session)):
    await delete_by_guid(guid, session)