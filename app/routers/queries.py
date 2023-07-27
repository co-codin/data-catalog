import asyncio
import json

from fastapi import APIRouter, Depends

from app.crud.crud_queries import (
    select_model_resource_attrs, match_linked_resources, filter_connected_resources, select_all_resources,
    check_alias_attrs_for_existence, create_query, get_query, get_identity_queries, alter_query,
    remove_query, check_owner_for_existence, create_query_execution, get_query_running_history,
    check_model_version_for_existence, check_on_query_owner, send_query_to_task_broker, select_conn_string,
    check_on_query_uniqueness, set_query_status, select_running_query_exec, terminate_query, get_query_to_run
)
from app.crud.crud_tag import remove_redundant_tags
from app.models.log import LogEvent, LogType
from app.models.queries import QueryRunningStatus
from app.schemas.log import LogIn
from app.schemas.queries import (
    LinkedResourcesIn, QueryIn, ModelResourceOut, QueryManyOut, QueryExecutionOut,
    FullQueryOut, QueryUpdateIn
)
from app.dependencies import db_session, ag_session, get_user, get_token
from app.services.log import add_log

router = APIRouter(
    prefix='/queries',
    tags=['queries']
)


@router.get('/linked_resources', response_model=list[ModelResourceOut])
async def read_linked_resources(
        linked_resources_in: LinkedResourcesIn, session=Depends(db_session), age_session=Depends(ag_session),
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
    model_resource_attrs = await select_model_resource_attrs(linked_resources_in.attribute_ids, session)
    if not model_resource_attrs:
        return await select_all_resources(linked_resources_in.model_version_id, session)

    db, ns, _ = model_resource_attrs[0].split('.', maxsplit=2)
    graph_name = f'{db}.{ns}'

    resource_names = {db_link.split('.', maxsplit=3)[2] for db_link in model_resource_attrs}
    loop = asyncio.get_running_loop()
    connected_resources = await loop.run_in_executor(
        None, match_linked_resources, resource_names, graph_name, age_session
    )
    connected_db_links = [f'{graph_name}.{connected_resource}' for connected_resource in connected_resources]
    model_resources = await filter_connected_resources(
        connected_db_links, linked_resources_in.model_version_id, session
    )
    return model_resources


@router.post('/')
async def add_query(query_in: QueryIn, session=Depends(db_session), token=Depends(get_token), user=Depends(get_user)):
    """
    1) check attrs for existence in the model version
    2) check owner guid for existence
    3) make a Query record in the db with QueryExecution(if needed) and Tag
    4) create json query for task broker using aliases, filter and having
    5) send query to task broker
    """
    await check_on_query_uniqueness(name=query_in.name, session=session)
    await check_alias_attrs_for_existence(query_in.aliases, session)
    await check_owner_for_existence(query_in.owner_guid, token)
    await check_model_version_for_existence(query_in.model_version_id, session)
    
    query = await create_query(query_in, session)

    if query_in.run_immediately:
        query_exec_guid = await create_query_execution(query, session)
        conn_string = await select_conn_string(query.model_version_id, session)
        await send_query_to_task_broker(
            query=query_in.dict(include={'aliases', 'filter', 'having'}), conn_string=conn_string,
            run_guid=query_exec_guid, token=token
        )

        await add_log(session, LogIn(
            type=LogType.QUERY_CONSTRUCTOR,
            log_name="Запуск запроса",
            text="Запрос {{{name}}} {{{guid}}} был запущен".format(
                query.name, query.guid
            ),
            identity_id=user['identity_id'],
            event=LogEvent.RUN_QUERY.value
        ))


@router.get('/', response_model=list[QueryManyOut])
async def read_queries(session=Depends(db_session), user=Depends(get_user)):
    return await get_identity_queries(user['identity_id'], session)


@router.get('/{guid}', response_model=FullQueryOut)
async def read_query(guid: str, session=Depends(db_session), token=Depends(get_token), user=Depends(get_user)):
    return await get_query(guid, session, user['identity_id'], token)


@router.put('/{guid}')
async def update_query(guid: str, query_update_in: QueryUpdateIn, session=Depends(db_session), user=Depends(get_user), token=Depends(get_token)):
    await check_owner_for_existence(query_update_in.owner_guid, token)
    await check_model_version_for_existence(query_update_in.model_version_id, session)
    await check_on_query_owner(guid, user['identity_id'], session)

    query = await alter_query(guid, query_update_in, session)
    asyncio.create_task(remove_redundant_tags())

    if query_update_in.run_immediately:
        query_exec_guid = await create_query_execution(query, session)
        conn_string = await select_conn_string(query.model_version_id, session)
        await send_query_to_task_broker(
            query=query_update_in.dict(include={'aliases', 'filter', 'having'}), conn_string=conn_string,
            run_guid=query_exec_guid, token=token
        )

        await add_log(session, LogIn(
            type=LogType.QUERY_CONSTRUCTOR,
            log_name="Запуск запроса",
            text="Запрос {{{name}}} {{{guid}}} был запущен".format(
                query.name, query.guid
            ),
            identity_id=user['identity_id'],
            event=LogEvent.RUN_QUERY.value
        ))


@router.get('/{guid}/executions/', response_model=list[QueryExecutionOut])
async def read_query_running_history(guid: str, session=Depends(db_session), user=Depends(get_user)):
    return await get_query_running_history(guid, user['identity_id'], session)


@router.delete('/{guid}')
async def delete_query(guid: str, session=Depends(db_session), user=Depends(get_user)):
    await remove_query(guid, user['identity_id'], session)


@router.put('/execs/{query_exec_guid}')
async def update_query_status(query_exec_guid: str, status: QueryRunningStatus, session=Depends(db_session)):
    await set_query_status(query_exec_guid, status, session)


@router.post('/{guid}/run')
async def run_query(guid: str, session=Depends(db_session), token=Depends(get_token), user=Depends(get_user)):
    await check_on_query_owner(guid, user['identity_id'], session)
    query_to_run = await get_query_to_run(guid, session)
    query_exec_guid = await create_query_execution(query_to_run, session)
    conn_string = await select_conn_string(query_to_run.model_version_id, session)
    await send_query_to_task_broker(
        query=json.loads(query_to_run.json), conn_string=conn_string,
        run_guid=query_exec_guid, token=token
    )

    await add_log(session, LogIn(
            type=LogType.QUERY_CONSTRUCTOR,
            log_name="Запуск запроса",
            text="Запрос {{{name}}} {{{guid}}} был запущен".format(
                query_to_run.name, query_to_run.guid
            ),
            identity_id=user['identity_id'],
            event=LogEvent.RUN_QUERY.value
        ))


@router.put('/{guid}/cancel')
async def cancel_query(guid: str, session=Depends(db_session), user=Depends(get_user)):
    await check_on_query_owner(guid, user['identity_id'], session)
    query_exec = await select_running_query_exec(guid, session)
    await terminate_query(query_exec.guid)

    await add_log(session, LogIn(
            type=LogType.QUERY_CONSTRUCTOR,
            log_name="Остановка запроса",
            text="Запрос {{{name}}} {{{guid}}} был остановлен".format(
                query_exec.query.name, query_exec.query.guid
            ),
            identity_id=user['identity_id'],
            event=LogEvent.STOP_QUERY.value
        ))
