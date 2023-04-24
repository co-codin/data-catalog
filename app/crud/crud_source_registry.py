import uuid
import logging
import requests

from typing import List, Dict, Iterable

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.schemas.source_registry import (
    SourceRegistryIn, SourceRegistryUpdateIn, SourceRegistryOut, CommentIn, CommentOut
)
from app.models.sources import SourceRegister, Tag, Comment
from app.config import settings

logger = logging.getLogger(__name__)


async def create_source_registry(source_registry: SourceRegistryIn, user_guid: str, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())
    source_registry_dict = source_registry.dict(exclude={'tags', 'comments'})

    source_registry_model = SourceRegister(**source_registry_dict, guid=guid)

    for tag in source_registry.tags:
        source_registry_model.tags.append(
            Tag(name=tag)
        )
    for comment in source_registry.comments:
        source_registry_model.comments.append(
            Comment(**comment.dict(), author_guid=user_guid)
        )

    session.add(source_registry_model)
    await session.commit()

    return source_registry_model.guid


async def edit_source_registry(guid: str, source_registry: SourceRegistryUpdateIn, session: AsyncSession):
    await session.execute(
        update(SourceRegister)
        .where(SourceRegister.guid == guid)
        .values(**source_registry.dict())
    )
    await session.commit()


async def remove_source_registry(guid: str, session: AsyncSession):
    await session.execute(
        delete(SourceRegister)
        .where(SourceRegister.guid == guid)
    )
    await session.commit()


async def read_all(token: str, session: AsyncSession) -> List[SourceRegistryOut]:
    source_registries = await session.execute(
        select(SourceRegister)
        .options(selectinload(SourceRegister.tags))
        .options(selectinload(SourceRegister.comments))
    )
    source_registries = source_registries.scalars().all()
    if not source_registries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    author_guids = {
        comment.author_guid
        for source_registry in source_registries
        for comment in source_registry.comments
    }

    source_registries_out = [SourceRegistryOut.from_orm(source_registry) for source_registry in source_registries]
    authors_data = await _get_authors_data_by_guids(author_guids, token)

    for source_registry in source_registries_out:
        _set_author_data(source_registry.comments, authors_data)
    return source_registries_out


async def read_by_guid(guid: str, token: str, session: AsyncSession) -> SourceRegistryOut:
    source_registry = await session.execute(
        select(SourceRegister)
        .options(selectinload(SourceRegister.tags))
        .options(selectinload(SourceRegister.comments))
        .filter(SourceRegister.guid == guid)
    )

    source_registry = source_registry.scalars().first()
    if not source_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    author_guids = {comment.author_guid for comment in source_registry.comments}
    source_registry_out = SourceRegistryOut.from_orm(source_registry)
    authors_data = await _get_authors_data_by_guids(author_guids, token)

    _set_author_data(source_registry_out.comments, authors_data)

    return source_registry_out


async def _get_authors_data_by_guids(guids: Iterable[str], token: str) -> Dict[str, Dict[str, str]]:
    response = requests.get(
        f'{settings.api_iam}/internal/users/',
        json={'guids': tuple(guids)},
        headers={"Authorization": f"Bearer {token}"}
    )
    authors_data = response.json()
    return authors_data


def _set_author_data(comments: Iterable[CommentOut], authors_data: Dict[str, Dict[str, str]]):
    for comment in comments:
        comment.author_first_name = authors_data[comment.author_guid]['first_name']
        comment.author_last_name = authors_data[comment.author_guid]['last_name']
        comment.author_middle_name = authors_data[comment.author_guid]['middle_name']
        comment.author_email = authors_data[comment.author_guid]['email']


async def create_comment(guid: str, author_guid: str, comment: CommentIn, session: AsyncSession) -> int:
    comment = Comment(**comment.dict(), author_guid=author_guid, source_guid=guid)

    session.add(comment)
    await session.commit()
    return comment.id


async def edit_comment(id_: int, comment: CommentIn, session: AsyncSession):
    await session.execute(
        update(Comment)
        .where(Comment.id == id_)
        .values(**comment.dict())
    )
    await session.commit()


async def remove_comment(id_: int, session: AsyncSession):
    await session.execute(
        delete(Comment)
        .where(Comment.id == id_)
    )
    await session.commit()


async def verify_comment_owner(id_: int, author_guid: str, session: AsyncSession):
    comment_from_db = await session.execute(
        select(Comment)
        .filter(Comment.id == id_)
    )
    comment_from_db = comment_from_db.scalars().first()
    if not comment_from_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if comment_from_db.author_guid != author_guid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


async def create_tag(guid: str, tag: str, session: AsyncSession) -> int:
    tag_model = Tag(name=tag, source_guid=guid)
    session.add(tag_model)
    await session.commit()
    return tag_model.id


async def remove_tag(id_: int, session: AsyncSession):
    await session.execute(
        delete(Tag)
        .where(Tag.id == id_)
    )
    await session.commit()
