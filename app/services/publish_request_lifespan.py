import json

from sqlalchemy import update

from app.models.queries import QueryExecution
from app.database import db_session


async def set_query_exec_status(body: bytes):
    body = json.loads(body)
    guid, status = body['guid'], body['status']

    async with db_session() as session:
        await session.execute(
            update(QueryExecution)
            .where(QueryExecution.guid == guid)
            .values(publish_status=status)
        )
