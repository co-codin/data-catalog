from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.nodes import LinkIn
from app.dependencies import neo4j_session
from app.crud.crud_link import add_link

router = APIRouter()


@router.post('/')
async def create_link(link_in: LinkIn, session: AsyncSession = Depends(neo4j_session)):
    link_ids = await add_link(link_in, session)
    return {
        'status': 'ok',
        'message': f'link {link_in.one_way_links[0].name} and {link_in.one_way_links[1].name} were created',
        'id1': link_ids[0],
        'id2': link_ids[1]
    }


@router.put('/hubs/')
async def update_link(link_in: LinkIn, session: AsyncSession = Depends(neo4j_session)):
    ...


@router.delete('/hubs/')
async def delete_link(link_in: LinkIn, session: AsyncSession = Depends(neo4j_session)):
    ...
