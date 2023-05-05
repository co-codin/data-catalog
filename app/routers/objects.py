from fastapi import APIRouter, Depends


from app.crud.crud_object import create_object
from app.schemas.objects import ObjectIn
from app.dependencies import db_session, get_user


router = APIRouter(
    prefix='/objects',
    tags=['object']
)


@router.post('/')
async def add_object(object_in: ObjectIn, session=Depends(db_session), _=Depends(get_user)):
    guid = await create_object(object_in, session)
    return {'guid': guid}
