from fastapi import APIRouter, Depends

from app.crud.crud_query_constructor import create_query_constructor, read_all, read_by_guid, edit_query_constructor, delete_by_guid
from app.dependencies import db_session, get_user
from app.schemas.query_constructor import QueryConstructorUpdateIn, QueryConstructorIn

router = APIRouter(
    prefix="/query_constructor",
    tags=['query constructor']
)


@router.post('/')
async def add_query_constructor(query_constructor_in: QueryConstructorIn, session=Depends(db_session),
                                _=Depends(get_user)):
    query_constructor = await create_query_constructor(query_constructor_in=query_constructor_in, session=session)
    return {'guid': query_constructor.guid}


@router.get('/')
async def read_query_constructors(session=Depends(db_session), _=Depends(get_user)):
    return await read_all(session)


@router.get('/{guid}')
async def get_query_constructor(guid: str, session=Depends(db_session), _=Depends(get_user)):
    return await read_by_guid(guid, session)


@router.put('/{guid}')
async def update_query_constructor(guid: str, query_constructor_update_in: QueryConstructorUpdateIn,
                                   session=Depends(db_session),
                       _=Depends(get_user)):
    await edit_query_constructor(guid, query_constructor_update_in, session)


@router.delete('/{guid}')
async def delete_query_constructor(guid: str, session=Depends(db_session), _=Depends(get_user)):
    await delete_by_guid(guid, session)
