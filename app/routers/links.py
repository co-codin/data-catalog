from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.schemas.link import LinkIn, LinkUpdateIn
from app.dependencies import neo4j_session
from app.crud.crud_link import add_link, edit_link, remove_link

router = APIRouter()


@router.post('/')
async def create_link(link_in: LinkIn, session: AsyncSession = Depends(neo4j_session)):
    link_uuid = await add_link(link_in, session)
    return {
        'status': 'ok',
        'message': f'links {link_in.main_link.name} and {link_in.paired_link.name} were created',
        'uuid': link_uuid,
    }


@router.put('/{link_uuid}/')
async def update_link(link_uuid: str, link_in: LinkUpdateIn, session: AsyncSession = Depends(neo4j_session)):
    await edit_link(link_uuid, link_in, session)
    return {'status': 'ok', 'message': 'link was updated'}


@router.delete('/{link_uuid}/')
async def delete_link(link_uuid: str, session: AsyncSession = Depends(neo4j_session)):
    await remove_link(link_uuid, session)
    return {'status': 'ok', 'message': f'link was deleted'}
