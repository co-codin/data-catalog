from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.nodes import SatIn, SatUpdateIn
from app.dependencies import neo4j_session
from app.crud.crud_sat import add_sat, edit_sat, remove_sat

router = APIRouter()


@router.post('/')
async def create_sat(sat_in: SatIn, session: AsyncSession = Depends(neo4j_session)):
    sat_uuid = await add_sat(sat_in, session)
    return {'status': 'ok', 'message': f'sat {sat_in.name} was created', 'uuid': sat_uuid}


@router.put('/{sat_uuid}/')
async def update_sat(sat_uuid: str, sat_in: SatUpdateIn, session: AsyncSession = Depends(neo4j_session)):
    sat_uuid = await edit_sat(sat_uuid, sat_in, session)
    return {'status': 'ok', 'message': f'sat was updated', 'uuid': sat_uuid}


@router.delete('/{sat_uuid}/')
async def delete_sat(sat_uuid: str, session: AsyncSession = Depends(neo4j_session)):
    sat_uuid = await remove_sat(sat_uuid, session)
    return {'status': 'ok', 'message': f'sat was deleted', 'id': sat_uuid}
