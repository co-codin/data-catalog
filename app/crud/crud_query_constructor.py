import uuid

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.crud.crud_tag import add_tags, update_tags
from app.models import QueryConstructor, QueryConstructorBody, QueryConstructorBodyField, ModelVersion
from app.schemas.query_constructor import QueryConstructorIn, QueryConstructorManyOut, QueryConstructorOut, \
    QueryConstructorUpdateIn


async def create_query_constructor(query_constructor_in: QueryConstructorIn, session: AsyncSession) -> QueryConstructor:
    guid = str(uuid.uuid4())

    query_constructor = QueryConstructor(
        **query_constructor_in.dict(exclude={'tags', 'fields', 'model_version_id', 'filters', 'aggregators'}),
        guid=guid
    )

    await add_tags(query_constructor, query_constructor_in.tags, session)
    session.add(query_constructor)

    query_constructor = await session.execute(
        select(QueryConstructor)
        .filter(QueryConstructor.guid == guid)
    )
    query_constructor = query_constructor.scalars().first()

    query_constructor_body = QueryConstructorBody(
        model_version_id=query_constructor_in.model_version_id,
        filters=query_constructor_in.filters,
        aggregators=query_constructor_in.aggregators,
        guid=guid,
        query_constructor_id=query_constructor.id
    )
    session.add(query_constructor_body)

    query_constructor_body = await session.execute(
        select(QueryConstructorBody)
        .filter(QueryConstructorBody.guid == guid)
    )
    query_constructor_body = query_constructor_body.scalars().first()

    for field in query_constructor_in.fields:
        guid = str(uuid.uuid4())
        query_constructor_body_field = QueryConstructorBodyField(
            model_resource_attribute_id=field,
            guid=guid,
            query_constructor_body_id=query_constructor_body.id
        )
        session.add(query_constructor_body_field)

    await session.commit()
    return query_constructor


async def read_all(session: AsyncSession) -> list[QueryConstructorManyOut]:
    query_constructors = await session.execute(
        select(QueryConstructor)
        .options(selectinload(QueryConstructor.tags))
        .options(selectinload(QueryConstructor.query_constructor_body)
                 .selectinload(QueryConstructorBody.model_version))
        .order_by(QueryConstructor.created_at)
    )
    query_constructors = query_constructors.scalars().all()

    return [QueryConstructorManyOut.from_orm(query_constructor) for query_constructor in query_constructors]


async def read_by_guid(guid: str, session: AsyncSession) -> QueryConstructorOut:
    query_constructor = await session.execute(
        select(QueryConstructor)
        .options(selectinload(QueryConstructor.tags))
        .options(joinedload(QueryConstructor.query_constructor_body)
                 .selectinload(QueryConstructorBody.model_version)
                 .selectinload(ModelVersion.model))
        .options(joinedload(QueryConstructor.query_constructor_body)
                 .joinedload(QueryConstructorBody.query_constructor_body_field))
        .filter(QueryConstructor.guid == guid)
    )

    query_constructor = query_constructor.scalars().first()

    if not query_constructor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    query_constructor_out = QueryConstructorOut.from_orm(query_constructor)

    return query_constructor_out


async def edit_query_constructor(guid: str, query_constructor_update_in: QueryConstructorUpdateIn,
                                 session: AsyncSession):
    query_constructor_update_in_data = {
        key: value for key, value in query_constructor_update_in.dict(exclude={'tags', 'fields', 'model_version_id',
                                                                               'filters', 'aggregators'}).items()
        if value is not None
    }

    await session.execute(
        update(QueryConstructor)
        .where(QueryConstructor.guid == guid)
        .values(
            **query_constructor_update_in_data,
        )
    )

    query_constructor = await session.execute(
        select(QueryConstructor)
        .options(selectinload(QueryConstructor.tags))
        .filter(QueryConstructor.guid == guid)
    )
    query_constructor = query_constructor.scalars().first()
    if not query_constructor:
        return

    await update_tags(query_constructor, session, query_constructor_update_in.tags)

    await session.execute(
        update(QueryConstructorBody)
        .where(QueryConstructorBody.guid == guid)
        .values(
            model_version_id=query_constructor_update_in.model_version_id,
            filters=query_constructor_update_in.filters,
            aggregators=query_constructor_update_in.aggregators,
        )
    )

    query_constructor_body = await session.execute(
        select(QueryConstructorBody)
        .options(selectinload(QueryConstructorBody.query_constructor_body_field))
        .filter(QueryConstructorBody.guid == guid)
    )
    query_constructor_body = query_constructor_body.scalars().first()

    if query_constructor_update_in.fields is not None:
        fields_update_in_set = set()
        for field in query_constructor_update_in.fields:
            fields_update_in_set.add(field)

        body_fields_set = {field for field in query_constructor_body.query_constructor_body_id}
        body_fields_dict = {field: field for field in query_constructor_body.query_constructor_body_id}

        fields_to_delete = body_fields_set - fields_update_in_set
        for field in fields_to_delete:
            query_constructor_body.query_constructor_body_id.remove(body_fields_dict[field])

        fields_to_create = fields_update_in_set - body_fields_set
        for field_in in query_constructor_update_in.fields:
            if field_in in fields_to_create:
                guid = str(uuid.uuid4())
                field = QueryConstructorBodyField(
                    model_resource_attribute_id=field_in,
                    guid=guid,
                    query_constructor_body_id=query_constructor_body.id
                )
                session.add(field)

        await session.commit()


async def delete_by_guid(guid: str, session: AsyncSession):
    await session.execute(
        delete(QueryConstructor)
        .where(QueryConstructor.guid == guid)
    )
    await session.commit()
