from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.nodes import LinkIn
from app.dependencies import neo4j_session

router = APIRouter()


@router.post('/')
async def create_link(link_in: LinkIn, session: AsyncSession = Depends(neo4j_session)):
    ...


@router.put('/hubs/')
async def update_link(link_in: LinkIn, session: AsyncSession = Depends(neo4j_session)):
    ...


@router.delete('/hubs/')
async def delete_link(link_in: LinkIn, session: AsyncSession = Depends(neo4j_session)):
    ...
