create_hub_query = "CREATE (hub:Entity {uuid: coalesce($uuid, randomUUID()), name: $name, desc: $desc, db: $db}) " \
                   "WITH $fields as fields_batch, hub " \
                   "UNWIND fields_batch as field " \
                   "CREATE (hub)-[:ATTR]->(:Field {name: field.name, desc: field.desc, db: field.db, attrs: field.attrs, dbtype: field.dbtype}) " \
                   "RETURN hub.uuid as uuid;"


match_link_query = "MATCH (e:Entity {uuid: $hub_uuid}) " \
                   "OPTIONAL MATCH (e)-[:LINK]->(l1:Link)-[:LINK]->(:Entity)-[:LINK]->(:Link)-[:LINK]->(e) " \
                   "RETURN l1.uuid as uuid;"


edit_hub_info_query = "MATCH (hub:Entity {uuid: $hub_uuid}) " \
                      "SET hub.name=$name, hub.desc=$desc, hub.db=$db " \
                      "RETURN hub.uuid as uuid;"


delete_hub_query = "MATCH (e:Entity {uuid: $hub_uuid}) " \
                   "OPTIONAL MATCH (e)-[:SAT]->(s:Sat)-[:ATTR]->(sf:Field) " \
                   "OPTIONAL MATCH (e)-[:ATTR]->(ef:Field) " \
                   "WITH e.uuid as uuid, sf, s, ef, e " \
                   "DETACH DELETE sf, s, ef, e " \
                   "RETURN uuid;"
