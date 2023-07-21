import logging
import clickhouse_connect

from app.config import settings

LOG = logging.getLogger(__name__)


class ClickhouseService:
    def __init__(self):
        self._conn_string = settings.clickhouse_connection_string
        self.client = None

    def connect(self):
        self.client = clickhouse_connect.get_client(dsn=settings.clickhouse_connection_string)

    def createPublishTable(self, guid: str):
        self.client.command(
            "CREATE TABLE IF NOT EXISTS {}_{} (query_id UInt32, publish_name String, publish_status String, published_at String, status String, finished_at String) ENGINE MergeTree ORDER BY query_id"
            .format("publish", guid)
        )

    async def dropPublishTable(self, guid: str):
        self.client.command(
            "DROP TABLE {}_{}".format("publish", guid)
        )

    def insert(self, guid, query_id, published_at, publish_name, publish_status, status, finished_at):
        data = [[query_id, published_at, publish_name, publish_status, status, finished_at]]
        self.client.insert('publish_'+guid, data, column_names=['query_id','published_at','publish_name','publish_status','status','finished_at'])

    def getByName(self, guid, publish_name):
        return self.client.query(
            "SELECT * FROM publish_{} WHERE publish_name = '{}'".format(guid, publish_name)
        )
