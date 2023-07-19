import logging
import psycopg
import asyncio
import clickhouse_connect

from clickhouse_connect.driver.exceptions import DatabaseError

from executor_service.errors import QueryNotRunning
from app.config import settings


LOG = logging.getLogger(__name__)


client = clickhouse_connect.get_client(dsn=settings.clickhouse_connection_string)

