from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = False
    log_dir: str = "/var/log/n3dwh/"
    log_name: str = "data_catalog.log"
    neo4j_connection_string: str = 'bolt://graphdb.lan:7687'

    class Config:
        env_prefix = "dwh_data_catalog_"
        case_sensitive = False


settings = Settings()
