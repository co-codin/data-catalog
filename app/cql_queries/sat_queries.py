create_sat_query = "MATCH (node {uuid: $ref_table_uuid}) " \
                   "WHERE node:Entity OR node:Link " \
                   "CREATE (sat:Sat {uuid: coalesce($uuid, randomUUID()), name: $name, desc: $desc, db: $db})<-[:SAT {on: [$ref_table_pk, $fk]}]-(node) " \
                   "WITH $fields as fields_batch, sat " \
                   "UNWIND fields_batch as field " \
                   "CREATE (sat)-[:ATTR]->(:Field {name: field.name, desc: field.desc, db: field.db, attrs: field.attrs, dbtype: field.dbtype}) " \
                   "RETURN sat.uuid as sat_uuid;"


edit_sat_info_query = "MATCH (sat:Sat {uuid: $sat_uuid})<-[r:SAT]-() " \
                      "SET sat.name=$name, sat.desc=$desc, sat.db=$db, r.on=[$ref_table_pk, $fk] " \
                      "RETURN sat.uuid as uuid;"


edit_sat_link_query = "MATCH (sat:Sat {uuid: $sat_uuid})<-[r:SAT]-() " \
                      "MATCH (node {uuid: $ref_table_uuid}) " \
                      "CREATE (sat)<-[:SAT {on: [$ref_table_pk, $fk]}]-(node) " \
                      "DELETE r " \
                      "RETURN node.uuid as uuid;"


delete_sat_query = "MATCH (sat:Sat {uuid: $sat_uuid}) " \
                   "OPTIONAL MATCH (sat)-[:ATTR]->(f:Field) " \
                   "OPTIONAL MATCH (sat)<-[:SAT]-(node) " \
                   "WHERE node:Entity OR node:Link " \
                   "WITH sat.uuid as uuid, sat, f " \
                   "DETACH DELETE sat, f " \
                   "RETURN uuid;"
