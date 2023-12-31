import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import contains_eager, load_only
from app.crud.crud_queries import (
    check_alias_attrs_for_existence, create_query, get_query, get_identity_queries, alter_query,
    select_query_to_delete, check_owner_for_existence, create_query_execution, get_query_running_history,
    check_model_version_for_existence, check_on_query_owner, send_query_to_task_broker, select_conn_string,
    check_on_query_uniqueness, set_query_status, select_running_query_exec, terminate_query, get_query_to_run,
    viewer_delete_query, owner_delete_query, is_allowed_to_view
)
from app.crud.crud_tag import remove_redundant_tags
from app.errors.query_errors import QueryIsNotRunningError, QueryNameAlreadyExist
from app.models.log import LogEvent, LogType, LogName, LogText
from app.models.queries import QueryRunningStatus, QueryExecution
from app.schemas.log import LogIn
from app.schemas.queries import QueryIn, QueryManyOut, QueryExecutionOut, FullQueryOut, QueryUpdateIn

from app.dependencies import db_session, get_user, get_token
from app.services.log import add_log

router = APIRouter(
    prefix='/queries',
    tags=['queries']
)


@router.post('/')
async def add_query(query_in: QueryIn, session=Depends(db_session), token=Depends(get_token), user=Depends(get_user)):
    """
    1) check attrs for existence in the model version
    2) check owner guid for existence
    3) make a Query record in the db with QueryExecution(if needed) and Tag
    4) create json query for task broker using aliases, filter and having
    5) send query to task broker
    """
    try:
        await check_on_query_uniqueness(name=query_in.name, session=session)
    except Exception:
        raise QueryNameAlreadyExist(query_in.name)
    await check_alias_attrs_for_existence(query_in.aliases, session)

    await check_owner_for_existence(query_in.owner_guid, token)
    await check_model_version_for_existence(query_in.model_version_id, session)

    query = await create_query(query_in, session)

    if query_in.run_immediately:
        query_exec_guid = await create_query_execution(query, session)
        conn_string = await select_conn_string(query.model_version_id, session)
        await send_query_to_task_broker(
            query=query_in.dict(include={'aliases', 'filter', 'having', 'distinct'}), conn_string=conn_string,
            run_guid=query_exec_guid, token=token
        )

        await add_log(session, LogIn(
            type=LogType.QUERY_CONSTRUCTOR.value,
            log_name=LogName.QUERY_RUN.value,
            text=LogText.QUERY_RUN.value.format(name=query.name),
            identity_id=user['identity_id'],
            event=LogEvent.RUN_QUERY_REQUEST.value,
            properties=json.dumps({'query_guid': query.guid})
        ))

    return query


@router.get('/', response_model=list[QueryManyOut])
async def read_queries(session=Depends(db_session), user=Depends(get_user), token=Depends(get_token)):
    return await get_identity_queries(user['identity_id'], token, session)


@router.get('/{guid}', response_model=FullQueryOut)
async def read_query(guid: str, session=Depends(db_session), token=Depends(get_token), user=Depends(get_user)):
    return await get_query(guid, session, user['identity_id'], token)


@router.put('/internal/mark-error/{guid}')
async def update_query(guid: str, session=Depends(db_session)):
    query_exec = await session.execute(
        select(QueryExecution).with_for_update(nowait=True)
        .join(QueryExecution.query)
        .options(load_only(QueryExecution.guid, QueryExecution.status))
        .options(contains_eager(QueryExecution.query))
        .where(QueryExecution.guid == guid)
    )
    query_exec = query_exec.scalars().first()

    query_exec.status = QueryRunningStatus.ERROR.value
    query_exec.query.status = QueryRunningStatus.ERROR.value
    session.add(query_exec)


@router.put('/{guid}')
async def update_query(guid: str, query_update_in: QueryUpdateIn, session=Depends(db_session), user=Depends(get_user),
                       token=Depends(get_token)):
    await check_owner_for_existence(query_update_in.owner_guid, token)
    await check_model_version_for_existence(query_update_in.model_version_id, session)
    await check_on_query_owner(guid, user['identity_id'], session)

    query = await alter_query(guid, query_update_in, session)
    asyncio.create_task(remove_redundant_tags())

    if query_update_in.run_immediately:
        query_exec_guid = await create_query_execution(query, session)
        conn_string = await select_conn_string(query.model_version_id, session)
        await send_query_to_task_broker(
            query=query_update_in.dict(include={'aliases', 'filter', 'having', 'distinct'}), conn_string=conn_string,
            run_guid=query_exec_guid, token=token
        )

        await add_log(session, LogIn(
            type=LogType.QUERY_CONSTRUCTOR.value,
            log_name=LogName.QUERY_RUN.value,
            text=LogText.QUERY_RUN.value.format(name=query.name),
            identity_id=user['identity_id'],
            event=LogEvent.RUN_QUERY_SUCCESS.value,
            properties=json.dumps({'query_guid': query.guid})
        ))


@router.get('/{guid}/executions/', response_model=list[QueryExecutionOut])
async def read_query_running_history(guid: str, session=Depends(db_session), user=Depends(get_user)):
    return await get_query_running_history(guid, user['identity_id'], session)


@router.delete('/{guid}')
async def delete_query(guid: str, session=Depends(db_session), user=Depends(get_user), token=Depends(get_token)):
    query = await select_query_to_delete(guid, session)
    if await is_allowed_to_view(user['identity_id'], query) and query.owner_guid != user['identity_id']:
        await viewer_delete_query(query.id, user['identity_id'], session)
    elif query.owner_guid == user['identity_id']:
        await owner_delete_query(query, user['identity_id'], token, session)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.put('/execs/{query_exec_guid}')
async def update_query_status(query_exec_guid: str, status: QueryRunningStatus, session=Depends(db_session)):
    await set_query_status(query_exec_guid, status, session)


@router.post('/{guid}/run')
async def run_query(guid: str, session=Depends(db_session), token=Depends(get_token), user=Depends(get_user)):
    await check_on_query_owner(guid, user['identity_id'], session)
    query_to_run = await get_query_to_run(guid, session)
    query_exec_guid = await create_query_execution(query_to_run, session)
    conn_string = await select_conn_string(query_to_run.model_version_id, session)

    try:
        await send_query_to_task_broker(
            query=json.loads(query_to_run.json), conn_string=conn_string,
            run_guid=query_exec_guid, token=token
        )
        await add_log(session, LogIn(
            type=LogType.QUERY_CONSTRUCTOR.value,
            log_name=LogName.QUERY_RUN.value,
            text=LogText.QUERY_RUN.value.format(name=query_to_run.name),
            identity_id=user['identity_id'],
            event=LogEvent.RUN_QUERY_SUCCESS.value,
            properties=json.dumps({'query_guid': query_to_run.guid})
        ))
    except Exception:
        await add_log(session, LogIn(
            type=LogType.QUERY_CONSTRUCTOR.value,
            log_name=LogName.QUERY_ERROR.value,
            text=LogText.QUERY_RUN_ERROR.value.format(name=query_to_run.name),
            identity_id=user['identity_id'],
            event=LogEvent.RUN_QUERY_FAILED.value,
            properties=json.dumps({'query_guid': query_to_run.guid})
        ))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Запрос не может быть запущен")


@router.put('/{guid}/cancel')
async def cancel_query(guid: str, session=Depends(db_session), user=Depends(get_user)):
    await check_on_query_owner(guid, user['identity_id'], session)

    try:
        query_exec = await select_running_query_exec(guid, session)
        await terminate_query(query_exec.guid)
    except Exception:
        raise QueryIsNotRunningError()
