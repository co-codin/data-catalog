import asyncio
import json
import uuid

from datetime import datetime
from typing import Iterable
from typing import Optional

from age import Age

from fastapi import HTTPException, status

from sqlalchemy import select, update, and_, func, delete
from sqlalchemy.orm import selectinload, joinedload, load_only
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.crud.crud_tag import add_tags, update_tags
from app.crud.crud_author import get_authors_data_by_guids
from app.errors.query_errors import QueryNameAlreadyExist
from app.models.queries import Query, QueryRunningStatus, QueryExecution, QueryViewer, query_viewers
from app.models.models import ModelResource, ModelResourceAttribute, ModelVersion
from app.models.sources import Model
from app.schemas.queries import (
    ModelResourceOut, AliasAttr, AliasAggregate, QueryIn, QueryManyOut, QueryOut, QueryModelManyOut,
    QueryModelVersionManyOut, FullQueryOut, QueryModelResourceAttributeOut, QueryExecutionOut, QueryUpdateIn
)
from app.age_queries.node_queries import construct_match_connected_tables, match_neighbor_tables
from app.schemas.tag import TagOut


async def select_model_resource_attrs(attr_ids: list[int], session: AsyncSession) -> list[str]:
    attrs = await session.execute(
        select(ModelResourceAttribute)
        .options(load_only(ModelResourceAttribute.db_link))
        .where(ModelResourceAttribute.id.in_(attr_ids))
    )
    attrs = attrs.scalars().all()
    return [attr.db_link for attr in attrs]


def match_linked_resources(resource_names: set[str], graph_name: str, age_session: Age) -> set[str]:
    constructed_tables = construct_match_connected_tables(resource_names)
    constructed_tables = constructed_tables.as_string(age_session.connection)

    age_session.setGraph(graph_name)
    cursor = age_session.execCypher(
        match_neighbor_tables.format(resources=constructed_tables),
        cols=['t_neighbor']
    )
    return {table[0]['name'] for table in cursor} | resource_names


async def filter_connected_resources(
        connected_resources: list[str], model_version_id: int, session: AsyncSession
) -> list[ModelResourceOut]:
    model_resources = await session.execute(
        select(ModelResource)
        .options(load_only(ModelResource.guid, ModelResource.name))
        .where(
            and_(
                ModelResource.model_version_id == model_version_id,
                ModelResource.db_link.in_(connected_resources)
            )
        )
    )
    model_resources = model_resources.scalars().all()
    return [ModelResourceOut.from_orm(model_resource) for model_resource in model_resources]


async def select_all_resources(model_version_id: int, session: AsyncSession) -> list[ModelResourceOut]:
    model_resources = await session.execute(
        select(ModelResource)
        .options(load_only(ModelResource.guid, ModelResource.name))
        .where(ModelResource.model_version_id == model_version_id)
    )
    model_resources = model_resources.scalars().all()
    return [ModelResourceOut.from_orm(model_resource) for model_resource in model_resources]


async def check_alias_attrs_for_existence(aliases: dict[str, AliasAttr | AliasAggregate], session: AsyncSession):
    db_links = set()
    for alias in aliases.values():
        try:
            db_link_split = alias.attr.db_link.split('.')
        except AttributeError:
            db_link_split = alias.aggregate.db_link.split('.')
        db_link = f"{db_link_split[0]}.{db_link_split[1]}.{db_link_split[-2]}.{db_link_split[-1]}"
        db_links.add(db_link)

    model_resource_attrs_count = await session.execute(
        select(func.count(ModelResourceAttribute.id))
        .where(ModelResourceAttribute.db_link.in_(db_links))
    )
    model_resource_attrs_count = model_resource_attrs_count.scalars().first()
    if len(db_links) != model_resource_attrs_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={'msg': "some of the given attributes don't exist"}
        )

async def check_on_query_uniqueness(name: str, session: AsyncSession, guid: Optional[str] = None):
    queries = await session.execute(
        select(Query)
        .where(Query.name.ilike(name))
    )
    queries = queries.scalars().all()
    for query in queries:
        if query.name == name and query.guid != guid:
            raise QueryNameAlreadyExist(name)


async def create_query(query_in: QueryIn, session: AsyncSession) -> Query:
    query_json = query_in.dict(include={'aliases', 'filter', 'having'})
    query = Query(
        guid=str(uuid.uuid4()),
        status=QueryRunningStatus.CREATED.value,
        **query_in.dict(include={'name', 'desc', 'model_version_id', 'owner_guid', 'filter_type'}),
        json=json.dumps(query_json)
    )

    await add_tags(query, query_in.tags, session)
    session.add(query)
    return query


async def create_query_execution(query: Query, session: AsyncSession):
    query_execution = QueryExecution(
        guid=str(uuid.uuid4()),
        status=QueryRunningStatus.RUNNING.value,
        started_at=datetime.utcnow(),
        status_updated_at=datetime.utcnow()
    )
    query.status = QueryRunningStatus.RUNNING.value
    query.executions.append(query_execution)
    session.add(query)


async def check_owner_for_existence(owner_guid: str, token: str):
    loop = asyncio.get_running_loop()
    identities = await loop.run_in_executor(None, get_authors_data_by_guids, (owner_guid,), token)
    try:
        _ = identities[owner_guid]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'msg': f'identity with guid: {owner_guid} is not found'}
        )


async def check_model_version_for_existence(model_version_id: int, session: AsyncSession):
    model_version_count = await session.execute(
        select(func.count(ModelVersion.id))
        .where(ModelVersion.id == model_version_id)
    )
    model_version_count = model_version_count.scalars().first()
    if model_version_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'msg': f'model version with id = {model_version_id} is not found'}
        )


async def is_allowed_to_view(identity_guid: str, query: Query) -> int | None:
    if identity_guid == query.owner_guid:
        return query.id

    for identity in query.viewers:
        if identity.guid == identity_guid:
            return query.id


async def get_identity_queries(identity_guid: str, session: AsyncSession) -> list[QueryManyOut]:
    queries = await session.execute(
        select(Query)
        .options(joinedload(Query.model_version, innerjoin=True).load_only(ModelVersion.id))
        .options(
            joinedload(Query.model_version, innerjoin=True).joinedload(ModelVersion.model, innerjoin=True)
            .load_only(Model.name)
        )
        .options(selectinload(Query.viewers))
        .options(selectinload(Query.tags))
    )
    queries = queries.scalars().all()

    is_allowed_to_see_to_queries = {
        await is_allowed_to_view(identity_guid, query): query
        for query in queries
    }

    return [
        QueryManyOut(
            id=query.id, guid=query.guid, name=query.name, model_name=query.model_version.model.name,
            updated_at=query.updated_at, status=query.status, desc=query.desc,
            tags=[TagOut.from_orm(tag) for tag in query.tags]
        )
        for is_allowed_to_see, query in is_allowed_to_see_to_queries.items()
        if is_allowed_to_see
    ]


async def get_query(guid: str, session: AsyncSession, identity_guid: str, token: str) -> FullQueryOut:
    query = await session.execute(
        select(Query)
        .options(
            joinedload(Query.model_version, innerjoin=True).load_only(ModelVersion.guid, ModelVersion.version)
        )
        .options(
            joinedload(Query.model_version, innerjoin=True).joinedload(ModelVersion.model, innerjoin=True)
            .load_only(Model.guid, Model.name)
        )
        .options(selectinload(Query.viewers))
        .options(selectinload(Query.tags))
        .where(Query.guid == guid)
    )
    query = query.scalars().first()
    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    is_allowed_to_see = await is_allowed_to_view(identity_guid, query)
    if not is_allowed_to_see:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    loop = asyncio.get_running_loop()

    identities = await loop.run_in_executor(None, get_authors_data_by_guids, (query.owner_guid,), token)
    identity = identities[query.owner_guid]
    owner_info = [
        identity[key]
        for key in ('first_name', 'last_name', 'middle_name', 'email')
        if identity[key] is not None
    ]

    model_version_out = QueryModelVersionManyOut.from_orm(query.model_version)
    model_out = QueryModelManyOut.from_orm(query.model_version.model)
    query_out = QueryOut.from_orm(query)

    json_query = json.loads(query.json)
    db_links = {}
    for alias in json_query['aliases'].values():
        try:
            json_db_link = alias['attr']['db_link']
        except KeyError:
            json_db_link = alias['aggregate']['db_link']

        db_link_split = json_db_link.split('.')
        db_link = f"{db_link_split[0]}.{db_link_split[1]}.{db_link_split[-2]}.{db_link_split[-1]}"
        db_links[db_link] = json_db_link

    model_resource_attrs = await session.execute(
        select(ModelResourceAttribute)
        .where(ModelResourceAttribute.db_link.in_(tuple(db_links.keys())))
    )
    model_resource_attrs = model_resource_attrs.scalars().all()

    attrs = [
        QueryModelResourceAttributeOut(
            id=attr.id, guid=attr.guid, name=attr.name, db_link=attr.db_link, json_db_link=db_links[attr.db_link]
        )
        for attr in model_resource_attrs
    ]

    return FullQueryOut(
        **query_out.dict(exclude={'json_'}),
        owner=" ".join(owner_info),
        json=query_out.json_,
        model=model_out.dict(),
        model_version=model_version_out.dict(),
        attrs=[attr for attr in attrs]
    )


async def get_query_running_history(guid: str, identity_guid: str, session: AsyncSession) -> list[QueryExecutionOut]:
    query = await session.execute(
        select(Query.id)
        .where(Query.guid == guid)
    )
    query_id = query.scalars().first()

    query_running_history = await session.execute(
        select(QueryExecution)
        .options(joinedload(QueryExecution.query, innerjoin=True).load_only(Query.guid, Query.owner_guid))
        .options(joinedload(QueryExecution.query, innerjoin=True).selectinload(Query.viewers))
        .where(QueryExecution.query_id == query_id)
    )
    query_running_history = query_running_history.scalars().all()
    if query_running_history:
        is_allowed_to_see = await is_allowed_to_view(identity_guid, query_running_history[0].query)
        if not is_allowed_to_see:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return [QueryExecutionOut.from_orm(query_execution) for query_execution in query_running_history]
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={'msg': 'query is not found'})


async def check_on_query_owner(guid: str, identity_guid: str, session: AsyncSession):
    query = await session.execute(
        select(Query)
        .options(load_only(Query.owner_guid))
        .where(Query.guid == guid)
    )
    query = query.scalars().first()
    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if query.owner_guid != identity_guid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


async def alter_query(guid: str, query_update_in: QueryUpdateIn, session: AsyncSession):
    query_update_in_data = {
        key: value for key, value in query_update_in.dict().items()
        if value is not None
    }

    query_json = {}
    if 'aliases' in query_update_in_data:
        query_json['aliases'] = query_update_in_data['aliases']

    if 'filter' in query_update_in_data:
        query_json['filter'] = query_update_in_data['filter']

    if 'having' in query_update_in_data:
        query_json['having'] = query_update_in_data['having']


    for key in ['aliases', 'filter', 'having']:
        if key in query_update_in_data:
            del query_update_in_data[key]


    session.execute(
        update(Query)
        .where(Query.guid == guid)
        .values(
           json=json.dumps(query_json),
            **query_update_in_data
        )
    )
    query = await session.execute(
        select(Query)
        .options(selectinload(Query.tags))
        .where(Query.guid == guid)
    )
    
    query = query.scalars().first()

    if query:
        await update_tags(query, session, query_update_in.tags)
        session.add(query)


async def remove_query(guid: str, identity_guid: str, session: AsyncSession):
    query = await session.execute(
        select(Query)
        .options(load_only(Query.owner_guid, Query.id))
        .where(Query.guid == guid)
    )
    query = query.scalars().first()

    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if query.owner_guid != identity_guid:
        query_viewer = await session.execute(
            select(QueryViewer)
            .where(QueryViewer.guid == identity_guid)
        )
        query_viewer = query_viewer.scalars().first()

        if not query_viewer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        await session.execute(
            delete(query_viewers)
            .where(QueryViewer.id == query_viewer.id)
            .where(Query.id == query.id)
        )

    else:
        await session.execute(
            delete(Query)
            .where(Query.guid == guid)
        )
    await session.commit()
