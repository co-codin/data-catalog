import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    port: int = 8000
    debug: bool = True
    log_dir: str = "/var/log/n3dwh/"
    log_name: str = "data_catalog.log"

    db_connection_string: str = "postgresql+asyncpg://postgres:dwh@db.lan:5432/data_catalog"
    db_migration_connection_string: str = "postgresql+psycopg2://postgres:dwh@db.lan:5432/data_catalog"

    api_iam: str = 'http://iam.lan:8000'
    api_task_broker: str = 'http://task-broker.lan:8000'
    api_query_executor: str = 'http://query-executor.lan:8000'

    encryption_key: str = 'e4f0d87c56a99e57d4470da7396783d7003cec28ef3abf0ff3a1daf37002470a'

    clickhouse_connection_string: str = os.environ.get('dwh_query_executor_db_sources_clickhouse', 'clickhouse://clickhouse:dwh@clickhouse.lan:8123/dwh')

    origins: list[str] = [
        '*'
    ]

    # age constants
    age_connection_string: str = 'postgresql://postgres:dwh@graphdb.lan:5432/postgres'

    mq_connection_string: str = 'amqp://dwh:dwh@rabbit.lan:5672'

    migration_exchange: str = 'graph_migration'
    migration_request_queue: str = 'migration_requests'
    migrations_result_queue: str = 'migration_results'

    publish_exchange: str = 'publish_exchange'
    publish_request_queue: str = 'publish_requests'
    publish_result_queue: str = 'publish_results'

    class Config:
        env_prefix = "dwh_data_catalog_"
        case_sensitive = False


settings = Settings()
