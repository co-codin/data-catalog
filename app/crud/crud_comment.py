import enum

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.schemas.source_registry import CommentIn

from app.models.sources import Comment


class CommentOwnerTypes(enum.Enum):
    source_registry = 0
    object_ = 1
    model = 2
    model_version = 3


async def create_comment(
        guid: str, author_guid: str, comment: CommentIn, comment_owner: CommentOwnerTypes, session: AsyncSession
) -> int:
    if comment_owner == CommentOwnerTypes.source_registry:
        comment = Comment(**comment.dict(), author_guid=author_guid, source_guid=guid)
    elif comment_owner == CommentOwnerTypes.model:
        comment = Comment(**comment.dict(), author_guid=author_guid, model_guid=guid)
    elif comment_owner == CommentOwnerTypes.model_version:
        comment = Comment(**comment.dict(), author_guid=author_guid, model_version_guid=guid)
    else:
        comment = Comment(**comment.dict(), author_guid=author_guid, object_guid=guid)

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
