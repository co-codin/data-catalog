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

    def createPublishTable(self):
        self.client.command(
            "CREATE TABLE IF NOT EXISTS {} (query_id UInt32, publish_name String, publish_status String, published_at String, status String, finished_at String) ENGINE MergeTree ORDER BY query_id"
            .format("publish")
        )

    def insert(self, query_id, published_at, publish_name, publish_status, status, finished_at):
        data = [[query_id, published_at, publish_name, publish_status, status, finished_at]]
        self.client.insert('publish', data, column_names=['query_id','published_at','publish_name','publish_status','status','finished_at'])

    def getByName(self, publish_name):
        return self.client.query(
            "SELECT * FROM publish WHERE publish_name = '{}'".format(publish_name)
        )

    def update(self, query_id, published_at, publish_name, publish_status, status, finished_at):
        self.client.update(
            "publish",
            query_id=query_id,
            published_at=published_at,
            publish_name=publish_name,
            publish_status=publish_status,
            status=status,
            finished_at=finished_at
        )
