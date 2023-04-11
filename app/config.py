from collections import namedtuple
from pydantic import BaseSettings
import os


Neo4jCreds = namedtuple('Neo4jCreds', ['username', 'password'])


class Settings(BaseSettings):
    port: int = 8000
    debug: bool = False
    log_dir: str = "/var/log/n3dwh/"
    log_name: str = "data_catalog.log"
    neo4j_connection_string: str = os.environ.get('DWH_DATA_CATALOG_NEO4J_CONNECTION_STRING', 'bolt://graphdb.lan:7687')
    neo4j_auth: Neo4jCreds = (os.environ.get('DWH_DATA_CATALOG_NEO4J_CONNECTION_USER', 'neo4j'), os.environ.get('DWH_DATA_CATALOG_NEO4J_CONNECTION_PASSWORD', 'dwh'))

    class Config:
        env_prefix = "dwh_data_catalog_"
        case_sensitive = False


settings = Settings()
