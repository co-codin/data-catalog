from collections import namedtuple
from typing import List

from pydantic import BaseSettings
import os


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

    origins: List[str] = [
        '*'
    ]

    class Config:
        env_prefix = "dwh_data_catalog_"
        case_sensitive = False


settings = Settings()
