from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.nodes import LinkIn
from app.dependencies import neo4j_session
from app.crud.crud_link import add_link, remove_link

router = APIRouter()


@router.post('/')
async def create_link(link_in: LinkIn, session: AsyncSession = Depends(neo4j_session)):
    link_uuids = await add_link(link_in, session)
    return {
        'status': 'ok',
        'message': f'links {link_in.one_way_links[0].name} and {link_in.one_way_links[1].name} were created',
        'uuid1': link_uuids[0],
        'uuid2': link_uuids[1]
    }


@router.delete('/{link_uuid}/')
async def delete_link(link_uuid: str, session: AsyncSession = Depends(neo4j_session)):
    await remove_link(link_uuid, session)
    return {
        'status': 'ok',
        'message': f'links were deleted',
    }
