match_model_resource_rels = """
    MATCH (t1:Table {name: %s })<-[r:ONE_TO_MANY]-(t2:Table)
    RETURN r.on as rel, t2.name as t2_name, id(r) as one_to_many_id
"""

set_link_between_nodes = """
    MATCH (t1:Table {name: %s})
    WITH t1
    MATCH (t2: Table {name: %s})
    WITH t1, t2
    
    MERGE (t1)-[r_one_to_many:ONE_TO_MANY {on: [%s, %s]}]->(t2)
    
    MERGE (t2)-[r_many_to_many:MANY_TO_ONE {on: [%s, %s]}]->(t1)
    RETURN id(r_one_to_many) as r_one_to_many_id
"""


delete_link_between_nodes = """
    MATCH (t1:Table)-[r_one_to_many:ONE_TO_MANY]->(t2:Table)-[r_many_to_one:MANY_TO_ONE]->(t1:Table)
    WHERE id(r_one_to_many) = %s 
    AND r_one_to_many.on[0] = r_many_to_one.on[1]
    AND r_one_to_many.on[1] = r_many_to_one.on[0]
    DELETE r_one_to_many, r_many_to_one
    RETURN id(r_one_to_many)
"""