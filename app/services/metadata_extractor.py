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
                    "where table_schema = 'dv_raw' and table_type = 'BASE TABLE' and table_schema not in ('pg_catalog', 'information_schema');",
                )
                table_names = await cursor.fetchall()
                return {res[0] for res in table_names}

    async def extract_created_at_updated_at(self, table_name: str) -> Tuple[datetime.datetime, datetime.datetime]:
        created_at = datetime.datetime.now()
        updated_at = datetime.datetime.now()
        return created_at, updated_at


class MetaDataExtractorFactory:
    _DRIVER_TO_METADATA_EXTRACTOR_TYPE = {
        'postgresql': PostgresExtractor
    }

    @classmethod
    def build(cls, conn_string: str) -> MetadataExtractor:
        driver = conn_string.split('://', maxsplit=1)[0]
        metadata_extractor_class = cls._DRIVER_TO_METADATA_EXTRACTOR_TYPE[driver]
        return metadata_extractor_class(conn_string)
