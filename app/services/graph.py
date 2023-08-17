import json
import typing
import logging

from age import Age
from collections import deque

from app.errors.errors import (
    NoNodeNameError, UnknownRelationTypeError, NoDBTableError,
    NoDBFieldError, CyclicPathError
)

LOG = logging.getLogger(__name__)


async def get_attr_db_info(session: Age, attr: str):
    """
    Get table and join chain for attribute
    :param attr: comma separated attributes list
    :param session:
    :return:
    """
    db, ns, attr = attr.split('.', maxsplit=2)
    session.setGraph(f'{db}.{ns}')
    current_obj, *remainder = attr.split('.')

    db_table = None
    db_field = None
    db_type = 'string'
    abac_attrs = None
    db_joins = []

    cursor = session.execCypher(
        "MATCH (o:Table {name: %s}) RETURN id(o) as node_id",
        cols=['node_id'],
        params=(current_obj,)
    )
    table = {'node_id': next(cursor)[0]}

    if table is None:
        raise NoNodeNameError('Table', current_obj)

    current_node_id = table['node_id']
    visited_node_ids = {current_node_id}

    while remainder:
        field, *remainder = remainder
        LOG.debug(f'{field}{remainder}')

        result = session.execCypher(
            "MATCH (o:Table)-[r]->(f) WHERE id(o) = %s RETURN f, r, o",
            cols=['f', 'r', 'o'],
            params=(current_node_id,)
        )
        by_name = {node['name']: (node, rel, obj) for node, rel, obj in result}
        if field not in by_name:
            raise NoNodeNameError('Field', field)
        node, rel, obj = by_name[field]

        match rel.label:
            case 'ATTR':
                db_table, db_field, db_type = obj['db'], node['db'], node['dbtype']
                abac_attrs = None
            case 'ONE_TO_MANY' | 'MANY_TO_ONE':
                db_joins.append(
                    {'table': obj['db'], 'on': tuple(rel['on'])}
                )
            case _:
                raise UnknownRelationTypeError(rel.type)

        current_node_id = int(node.id)

        if current_node_id in visited_node_ids:
            raise CyclicPathError(attr)
        visited_node_ids.add(current_node_id)

    if db_table is None:
        raise NoDBTableError(attr)
    if db_field is None:
        raise NoDBFieldError(attr)

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
        'type': db_type,
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
