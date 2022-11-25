from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from app.config import settings
from app.errors import NoNeo4jConnection

driver = AsyncGraphDatabase.driver(settings.neo4j_connection_string)


async def neo4j_session():
    async with driver.session(database=settings.neo4j_db_name) as session:
        try:
            yield session
        except (ServiceUnavailable, ValueError):
            raise NoNeo4jConnection(settings.neo4j_connection_string)
