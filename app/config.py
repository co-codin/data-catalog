from pydantic import BaseSettings


class Settings(BaseSettings):
    NEO4J_CONNECTION_STRING: str = 'bolt://graph_db:7687'


settings = Settings()
