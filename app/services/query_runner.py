import logging
import psycopg
import asyncio
import clickhouse_connect

from abc import ABC, abstractmethod
from typing import List, AsyncIterable
from clickhouse_connect.driver.exceptions import DatabaseError

from executor_service._msgpack_io import msgpack_writer
from executor_service.errors import QueryNotRunning
from executor_service.settings import settings

LOG = logging.getLogger(__name__)


class QueryRunner(ABC):
    @abstractmethod
    def __init__(self, query_id: int):
        self._query_id = query_id

    @property
    def db_app_name(self):
        return f'sdwh_{self._query_id}'

    @abstractmethod
    async def execute_to_file(self, query: str, write_to: str):
        ...

    @abstractmethod
    async def cancel(self, query_guid: str):
        ...

    @staticmethod
    async def _save_to_dir(write_to: str, col_names: List, col_types: List, rows: AsyncIterable):
        with msgpack_writer(write_to) as writer:
            # first two rows name and types
            writer.writerow(col_names)
            writer.writerow(col_types)

            async for record in rows:
                writer.writerow(record)


class ClickHouseRunner(QueryRunner):
    def __init__(self, query_id: int):
        super().__init__(query_id)
        self._conn_string = settings.db_sources['clickhouse']

    @staticmethod
    async def _row_gen(rows):
        for row in rows:
            yield row

    async def execute_to_file(self, query: str, write_to: str):
        query_result = await asyncio.to_thread(self._execute_to_file, query)
        col_names = query_result.column_names
        col_types = [col_type.base_type for col_type in query_result.column_types]
        rows = self._row_gen(rows=query_result.result_rows)
        await self._save_to_dir(write_to, col_names=col_names, col_types=col_types, rows=rows)

    def _execute_to_file(self, query: str):
        client = clickhouse_connect.get_client(dsn=self._conn_string)
        try:
            result = client.query(
                query,
                settings={'replace_running_query': 1, 'query_id': self.db_app_name}
            )
        except DatabaseError as db_err:
            if "Code: 394" in str(db_err):  # if query was canceled
                raise psycopg.errors.QueryCanceled()
            raise db_err
        finally:
            client.close()
        return result

    async def cancel(self, query_guid: str):
        await asyncio.to_thread(self._cancel, query_guid)

    def _cancel(self, query_guid: str):
        client = clickhouse_connect.get_client(dsn=self._conn_string)
        try:
            res = client.query(
                "select query_id, query "
                "from system.processes "
                "where query_id=%s",
                (self.db_app_name,)
            )
            try:
                row = res.first_row
            except IndexError:
                raise QueryNotRunning(query_id=self._query_id)

            pid, sql = row
            LOG.info(f'Cancelling query {self._query_id} {query_guid} having db pid {pid} running query {sql}')
            client.query(
                "kill query "
                "where query_id=%s",
                (pid,)
            )
        finally:
            client.close()
