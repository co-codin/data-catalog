get_node_field_ids_query = "MATCH (node {uuid: $node_uuid})-[:ATTR]->(f:Field) " \
                           "RETURN ID(f);"


add_fields_hub_query = "MATCH (node {uuid: $node_uuid}) " \
                       "WITH $fields as fields_batch, node " \
                       "UNWIND fields_batch as field " \
                       "CREATE (node)-[:ATTR]->(f:Field {name: field.name, desc: field.desc, db: field.db, attrs: field.attrs, dbtype: field.dbtype});"


edit_fields_hub_query = "MATCH (node {uuid: $node_uuid}) " \
                        "WITH $fields as fields_batch, node " \
                        "UNWIND fields_batch as field " \
                        "MATCH (node)-[:ATTR]->(f:Field) " \
                        "WHERE ID(f)=field.id " \
                        "SET f.name=field.name, f.desc=field.desc, f.db=field.db, f.attrs=field.attrs, f.dbtype=field.dbtype;"


delete_fields_hub_query = "WITH $fields as fields_batch " \
                          "UNWIND fields_batch as field_id " \
                          "MATCH (node {uuid: $node_uuid})-[:ATTR]->(f:Field) " \
                          "WHERE ID(f)=field_id " \
                          "DETACH DELETE f;"

