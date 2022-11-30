from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False
    log_dir: str = "/var/log/n3dwh/"
    log_name: str = "data_catalog.log"
    neo4j_connection_string: str = 'bolt://graph_db:7687'


settings = Settings()
