from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.nodes import SatIn, SatUpdateIn
from app.dependencies import neo4j_session
from app.crud.crud_sat import add_sat, edit_sat, remove_sat

router = APIRouter()


@router.post('/')
async def create_sat(sat_in: SatIn, session: AsyncSession = Depends(neo4j_session)):
    sat_id = await add_sat(sat_in, session)
    return {'status': 'ok', 'message': f'entity {sat_in.name} was created', 'id': sat_id}


@router.put('/{sat_name}/')
async def update_sat(sat_name: str, sat_in: SatUpdateIn, session: AsyncSession = Depends(neo4j_session)):
    sat_id = await edit_sat(sat_name, sat_in, session)
    return {'status': 'ok', 'message': f'sat {sat_name} was updated', 'id': sat_id}


@router.delete('/{sat_name}/')
async def delete_sat(sat_name: str, session: AsyncSession = Depends(neo4j_session)):
    sat_id = await remove_sat(sat_name, session)
    return {'status': 'ok', 'message': f'sat {sat_name} was deleted', 'id': sat_id}
