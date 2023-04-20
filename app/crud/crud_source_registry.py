import uuid
import logging

from typing import List

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.schemas.source_registry import SourceRegistryIn, SourceRegistryUpdateIn, SourceRegistryOut, CommentIn
from app.models.sources import SourceRegister, Tag, Comment

logger = logging.getLogger(__name__)


async def create_source_registry(source_registry: SourceRegistryIn, session: AsyncSession) -> str:
    guid = str(uuid.uuid4())
    input_dict = source_registry.dict(exclude={'tags', 'comments'})

    source_registry_model = SourceRegister(**input_dict, guid=guid)

    for tag in source_registry.tags:
        logger.info(f'tag: {tag}')
        source_registry_model.tags.append(
            Tag(name=tag)
        )
    for comment in source_registry.comments:
        logger.info(f'comment: {comment}')
        source_registry_model.comments.append(
            Comment(**comment.dict(exclude={'_id'}))
        )

    session.add(source_registry_model)
    await session.commit()

    return source_registry_model.guid


async def edit_source_registry(guid: str, source_registry: SourceRegistryUpdateIn, session: AsyncSession):
    await session.execute(
        update(SourceRegister)
        .where(SourceRegister.guid == guid)
        .values(**source_registry.dict(exclude={'tags', 'comments'}))
    )
    await session.commit()


async def remove_source_registry(guid: str, session: AsyncSession):
    await session.execute(
        delete(SourceRegister)
        .where(SourceRegister.guid == guid)
    )
    await session.commit()


async def read_all(session: AsyncSession) -> List[SourceRegistryOut]:
    source_registries = await session.execute(
        select(SourceRegister)
        .options(selectinload(SourceRegister.tags))
        .options(selectinload(SourceRegister.comments))
    )
    source_registries = source_registries.scalars().all()
    if not source_registries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return [SourceRegistryOut.from_orm(source_registry) for source_registry in source_registries]


async def read_by_guid(guid: str, session: AsyncSession) -> SourceRegistryOut:
    source_registry = await session.execute(
        select(SourceRegister)
        .options(selectinload(SourceRegister.tags))
        .options(selectinload(SourceRegister.comments))
        .filter(SourceRegister.guid == guid)
    )

    source_registry = source_registry.scalars().first()
    if not source_registry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    source_registry_out = SourceRegistryOut.from_orm(source_registry)
    return source_registry_out


async def create_comment(guid: str, author_guid: str, comment: CommentIn, session: AsyncSession) -> id:
    comment = Comment(**comment.dict(), author_guid=author_guid, source_guid=guid)

    session.add(comment)
    await session.commit()
    return comment.id


async def edit_comment(id_: int, author_guid: str, comment: CommentIn, session: AsyncSession):
    await _verify_comment_owner(id_, author_guid, session)

    await session.execute(
        update(Comment)
        .where(Comment.id == id_)
        .values(**comment.dict())
    )
    await session.commit()


async def remove_comment(id_: int, author_guid: str, session: AsyncSession):
    await _verify_comment_owner(id_, author_guid, session)

    await session.execute(
        delete(Comment)
        .where(Comment.id == id_)
    )
    await session.commit()


async def _verify_comment_owner(id_: int, author_guid: str, session: AsyncSession):
    comment_from_db = await session.execute(
        select(Comment)
        .filter(Comment.id == id_)
    )
    comment_from_db = comment_from_db.scalars().first()
    if not comment_from_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if comment_from_db.author_guid != author_guid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


async def create_tag(guid: str, tag: str, session: AsyncSession):
    tag_model = Tag(name=tag, source_gid=guid)
    session.add(tag_model)
    await session.commit()


async def remove_tag(id_: int, session: AsyncSession):
    await session.execute(
        delete(Tag)
        .where(Tag.id == id_)
    )
    await session.commit()
