import asyncio

from fastapi import APIRouter, Depends

from app.crud.crud_queries import (
    select_model_resource_attrs, match_linked_resources, filter_connected_resources, select_all_resources,
    check_alias_attrs_for_existence, create_query, get_query, get_identity_queries, alter_query,
    remove_query, check_owner_for_existence, create_query_execution, get_query_running_history,
    check_model_version_for_existence, check_on_query_owner, check_on_query_uniqueness
)
from app.crud.crud_tag import remove_redundant_tags
from app.schemas.queries import (
    AllowedResourcesIn, QueryIn, ModelResourceOut, QueryManyOut, QueryExecutionOut,
    FullQueryOut, QueryUpdateIn
)
from app.dependencies import db_session, ag_session, get_user, get_token

router = APIRouter(
    prefix='/queries',
    tags=['queries']
)


@router.get('/allowed_resources', response_model=list[ModelResourceOut])
async def read_allowed_resources(
        allowed_resources_in: AllowedResourcesIn, session=Depends(db_session), age_session=Depends(ag_session),
        _=Depends(get_user)
):
    """
    1) select model resource attributes db links from db
    2) take graph_name from db_link field
    3) take resource names from db_link field
    4) set required graph
    5) match all directly connected tables with the ones from step 3
    6) filter them with model version id and db_link field
    """
    model_resource_attrs = await select_model_resource_attrs(allowed_resources_in.attribute_ids, session)
    if not model_resource_attrs:
        return await select_all_resources(allowed_resources_in.model_version_id, session)

    db, ns, _ = model_resource_attrs[0].split('.', maxsplit=2)
    graph_name = f'{db}.{ns}'

    resource_names = {db_link.split('.', maxsplit=3)[2] for db_link in model_resource_attrs}
    loop = asyncio.get_running_loop()
    connected_resources = await loop.run_in_executor(
        None, match_linked_resources, resource_names, graph_name, age_session
    )
    connected_db_links = [f'{graph_name}.{connected_resource}' for connected_resource in connected_resources]
    model_resources = await filter_connected_resources(
        connected_db_links, allowed_resources_in.model_version_id, session
    )
    return model_resources


@router.post('/')
async def add_query(query_in: QueryIn, session=Depends(db_session), token=Depends(get_token)):
    """
    1) check attrs for existence in the model version
    2) check owner guid for existence
    3) make a Query record in the db with QueryExecution(if needed) and Tag
    4) create json query for task broker using aliases, filter and having
    5) send query to task broker
    """
    await check_on_query_uniqueness(
        name=query_in.name,
        session=session
    )
    await check_alias_attrs_for_existence(query_in.aliases, session)
    await check_owner_for_existence(query_in.owner_guid, token)
    await check_model_version_for_existence(query_in.model_version_id, session)
    query = await create_query(query_in, session)
    if query_in.run_immediately:
        await create_query_execution(query, session)
        # send query to task broker


@router.get('/', response_model=list[QueryManyOut])
async def read_queries(session=Depends(db_session), user=Depends(get_user)):
    return await get_identity_queries(user['identity_id'], session)


@router.get('/{guid}', response_model=FullQueryOut)
async def read_query(guid: str, session=Depends(db_session), token=Depends(get_token), user=Depends(get_user)):
    return await get_query(guid, session, user['identity_id'], token)


@router.put('/{guid}')
async def update_query(
        guid: str, query_update_in: QueryUpdateIn, session=Depends(db_session), token=Depends(get_token),
        user=Depends(get_user)
):
    await check_owner_for_existence(query_update_in.owner_guid, token)
    await check_model_version_for_existence(query_update_in.model_version_id, session)
    await check_on_query_owner(guid, user['identity_id'], session)
    await alter_query(guid, query_update_in, session)
    asyncio.create_task(remove_redundant_tags())


@router.get('/{guid}/executions/', response_model=list[QueryExecutionOut])
async def read_query_running_history(guid: str, session=Depends(db_session), user=Depends(get_user)):
    return await get_query_running_history(guid, user['identity_id'], session)


@router.delete('/{guid}')
async def delete_query(guid: str, session=Depends(db_session), user=Depends(get_user)):
    await remove_query(guid, user['identity_id'], session)
