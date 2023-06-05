import asyncio

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.crud.crud_source_registry import _get_authors_data_by_guids, _set_author_data, update_tags
from app.models.sources import Field
from app.schemas.objects import FieldOut, FieldUpdateIn


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
            None, _get_authors_data_by_guids, author_guids, token
        )
        _set_author_data(field.comments, authors_data)

    return FieldOut.from_orm(field)


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
        .values(**field_update.dict(exclude={'tags'}))
    )

    await update_tags(field_model, session, field_update.tags)
