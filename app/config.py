import os

from collections import namedtuple
from typing import List

from pydantic import BaseSettings

Neo4jCreds = namedtuple('Neo4jCreds', ['username', 'password'])


class Settings(BaseSettings):
    port: int = 8000
    debug: bool = True
    log_dir: str = "/var/log/n3dwh/"
    log_name: str = "data_catalog.log"
    neo4j_connection_string: str = 'bolt://graphdb.lan:7687'
    neo4j_auth: Neo4jCreds = (os.environ.get('dwh_data_catalog_neo4j_connection_user', 'neo4j'),
                              os.environ.get('dwh_data_catalog_neo4j_connection_password', 'dwh'))

    db_connection_string: str = "postgresql+asyncpg://postgres:dwh@db.lan:5432/data_catalog"
    db_migration_connection_string: str = "postgresql+psycopg2://postgres:dwh@db.lan:5432/data_catalog"

    api_iam: str = 'http://iam.lan:8000'
    api_graph_db_migrater: str = 'http://graph_db_migrater.lan:8081'

    encryption_key: str = 'e4f0d87c56a99e57d4470da7396783d7003cec28ef3abf0ff3a1daf37002470a'

    origins: List[str] = [
        '*'
    ]

    # age constants
    age_conn_string: str = 'postgresql://postgres:dwh@graphdb.lan:5432/postgres'

    mq_connection_string: str = 'amqp://dwh:dwh@rabbit.lan:5672'
    migration_exchange = 'graph_migration'
    migration_request_queue = 'migration_requests'
    migrations_result_queue = 'migration_results'

    class Config:
        env_prefix = "dwh_data_catalog_"
        case_sensitive = False


settings = Settings()
