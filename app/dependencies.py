from neo4j import GraphDatabase
from app.config import settings

driver = GraphDatabase.driver(settings.NEO4J_CONNECTION_STRING)


def neo4j_session():
    with driver.session() as session:
        yield session
