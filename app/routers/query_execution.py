from fastapi import APIRouter, Depends
from typing import Dict
from app.models.queries import QueryExecution
from app.dependencies import db_session, get_user
from sqlalchemy import update
from app.services.clickhouse_service import ClickhouseService




router = APIRouter(
    prefix='/query_executions',
    tags=['query executions']
)


@router.put('/{guid}/publish', response_model=Dict[str, str])
async def publish_query_execution(
        guid: str,  publish_name: str, session=Depends(db_session), _=Depends(get_user)
):
   '''
    должна быть опция "перезатирать одноименную публикацию". 
    Если опция активна, то если в хранилище есть публикация с точно таким же именем,
    то мы меняем текущую публикацию с таким же именем на текущий результат.
     Если публикация неактивна, но в хранилище есть публикация с таким же именем,
 то мы должны предупредить пользователя об этом и попросить изменить имя текущей публикации.
     По умолчанию опция активна. '''
   
#    clickhouseService = ClickhouseService
#    clickhouseService.connect()
#    clickhouseService.createTable()


   await session.execute(
        update(QueryExecution)
        .where(QueryExecution.guid == guid)
        .values(
            publish_name=publish_name
        )
    )
