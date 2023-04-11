from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from app.config import settings
from app.errors import NoNeo4jConnection

driver = AsyncGraphDatabase.driver(settings.neo4j_connection_string, auth=settings.neo4j_auth)


async def neo4j_session():
    async with driver.session() as session:
        try:
            yield session
        except (ServiceUnavailable):
            raise NoNeo4jConnection(settings.neo4j_connection_string)
