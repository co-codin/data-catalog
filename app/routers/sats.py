from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.nodes import SatIn
from app.dependencies import neo4j_session

router = APIRouter()


@router.post('/')
async def create_sat(sat_in: SatIn, session: AsyncSession = Depends(neo4j_session)):
    ...


@router.post('/{sat_name}/')
async def update_sat(sat_name: str, sat_in: SatIn, session: AsyncSession = Depends(neo4j_session)):
    ...


@router.delete('/{sat_name}/')
async def delete_sat(sat_name: str, session: AsyncSession = Depends(neo4j_session)):
    ...
