import json

import typing
import logging

from neo4j import Session
from collections import deque


LOG = logging.getLogger(__name__)


def get_attr_db_info(session: Session, attr: str):
    """
    Get table and join chain for attribute
    :param attr: comma separated attributes list
    :param session:
    :return:
    """
    current_obj, *remainder = attr.split('.')

    db_table = None
    db_field = None
    abac_attrs = None
    db_joins = []

    result = session.run("MATCH (o:Entity {name: $name}) RETURN id(o) as node_id", name=current_obj)
    current_node_id = result.single()['node_id']

    while remainder:
        field, *remainder = remainder
        LOG.debug(f'{field}{remainder}')

        result = session.run("MATCH (o)-[r]->(f) WHERE id(o) = $node RETURN f, r, o", node=int(current_node_id))
        by_name = {node['name']: (node, rel, obj) for node, rel, obj in result}
        if field not in by_name:
            raise Exception(f'Field {field} does not exist')
        node, rel, obj = by_name[field]

        if rel.type == 'ATTR':
            db_table = obj['db']
            db_field = node['db']
            abac_attrs = node.get('attrs')
        elif rel.type == 'SAT':
            db_joins.append(
                {'table': obj['db'], 'on': tuple(rel['on'])}
            )
        elif rel.type == 'LINK':
            db_joins.append(
                {'table': obj['db'], 'on': tuple(rel['on'])}
            )
            result = session.run("MATCH (o)-[r]->(n) WHERE id(o) = $node RETURN n, r, o", node=int(node.element_id))
            node, rel, obj = result.peek()
            db_joins.append(
                {'table': obj['db'], 'on': tuple(rel['on'])}
            )
        else:
            raise Exception(f'Unknown relation {rel.type}')

        current_node_id = node.element_id

    if abac_attrs:
        abac_attrs = json.loads(abac_attrs)
    else:
        abac_attrs = []

    return {
        'table': {
            'name': db_table,
            'relation': optimize_join_chain(db_joins, db_table),
        },
        'field': db_field,
        'type': 'string',
        'attributes': abac_attrs,
    }


def optimize_join_chain(db_joins: typing.List[dict], db_table: str):
    """
    Optimize join chain by removing redundant tables
    """
    if not db_joins:
        return db_joins

    db_join_line = deque()
    for join in db_joins:
        db_join_line.append(join['table'])
        db_join_line.extend(join['on'])
    db_join_line.append(db_table)

    optimized_line = deque([db_join_line.popleft(), db_join_line.popleft()])
    while len(db_join_line) >= 3:
        lk, table, rk = db_join_line.popleft(), db_join_line.popleft(), db_join_line.popleft()
        if lk != rk:
            optimized_line.extend((lk, table, rk))
        else:
            pass
    optimized_line.extend(db_join_line)

    result = []
    optimized_line.pop()
    while optimized_line:
        result.append({
            'table': optimized_line.popleft(),
            'on': (optimized_line.popleft(), optimized_line.popleft())
        })

    return result
