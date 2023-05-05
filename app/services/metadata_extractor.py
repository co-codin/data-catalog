import datetime
import psycopg

from typing import Set, Tuple
from abc import ABC, abstractmethod


class MetadataExtractor(ABC):
    @abstractmethod
    def __init__(self, conn_string: str):
        self._conn_string = conn_string

    @abstractmethod
    async def extract_table_names(self) -> Set[str]:
        ...

    @abstractmethod
    async def extract_created_at_updated_at(self, table_name: str) -> Tuple[str, str]:
        ...


class PostgresExtractor(MetadataExtractor):
    def __init__(self, conn_string: str):
        super().__init__(conn_string)

    async def extract_table_names(self) -> Set[str]:
        async with await psycopg.AsyncConnection.connect(self._conn_string) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "select table_name "
                    "from information_schema.tables "
                    "where table_schema = %s;",
                    ('public',)
                )
                table_names = await cursor.fetchall()
                return {res[0] for res in table_names}

    async def extract_created_at_updated_at(self, table_name: str) -> Tuple[datetime.datetime, datetime.datetime]:
        created_at = datetime.datetime.now()
        updated_at = datetime.datetime.now()
        return created_at, updated_at
