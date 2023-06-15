import asyncio

from datetime import datetime

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.crud.crud_tag import update_tags
from app.models.sources import Field
from app.schemas.comment import CommentOut
from app.schemas.objects import FieldOut, FieldUpdateIn
from app.constants.data_types import ID_TO_SYS_DATA_TYPE
from app.schemas.tag import TagOut


async def select_field(field_guid: str, token: str, session: AsyncSession) -> FieldOut:
    field = await session.execute(
        select(Field)
        .options(selectinload(Field.tags), selectinload(Field.comments))
        .where(Field.guid == field_guid)
    )
    field = field.scalars().first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if field.comments:
        author_guids = {comment.author_guid for comment in field.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, get_authors_data_by_guids, author_guids, token
        )
        set_author_data(field.comments, authors_data)

    field = FieldOut(
        guid=field.guid, is_key=field.is_key, name=field.name,
        type=ID_TO_SYS_DATA_TYPE.get(field.data_type_id, None), length=len(field.name), owner=field.owner,
        desc=field.desc, local_updated_at=field.local_updated_at, synchronized_at=field.synchronized_at,
        source_updated_at=field.source_updated_at, source_created_at=field.source_created_at, db_path=field.db_path,
        tags=[TagOut.from_orm(tag) for tag in field.tags],
        comments=[CommentOut.from_orm(comment) for comment in field.comments]
    )

    return field


async def alter_field(field_guid: str, field_update: FieldUpdateIn, session: AsyncSession):
    field_model = await session.execute(
        select(Field)
        .options(selectinload(Field.tags))
        .where(Field.guid == field_guid)
    )
    field_model = field_model.scalars().first()

    await session.execute(
        update(Field)
        .where(Field.guid == field_guid)
        .values(
            **field_update.dict(exclude={'tags'}), local_updated_at=datetime.utcnow()
        )
    )

    await update_tags(field_model, session, field_update.tags)
