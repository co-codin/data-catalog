from pydantic import BaseSettings


class Settings(BaseSettings):
    neo4j_connection_string: str = 'bolt://graph_db:7687'
    neo4j_db_name: str = 'neo4j'


settings = Settings()
