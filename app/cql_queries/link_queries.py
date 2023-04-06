create_link_query = "MATCH (hub1:Entity {uuid: $main_link.ref_table_uuid }) " \
                    "MATCH (hub2:Entity {uuid: $paired_link.ref_table_uuid }) " \
                    "CREATE (hub1)-[:LINK {on: [$main_link.ref_table_pk, $main_link.fk]}]->(link1:Link {uuid: coalesce($uuid, randomUUID()), name: $main_link.name, desc: $main_link.desc, db: $db})-[:LINK {on: [$paired_link.fk, $paired_link.ref_table_pk]}]->(hub2) " \
                    "CREATE (hub2)-[:LINK {on: [$paired_link.ref_table_pk, $paired_link.fk]}]->(link2:Link {name: $paired_link.name, desc: $paired_link.desc, db: $db})-[:LINK {on: [$main_link.fk, $main_link.ref_table_pk]}]->(hub1) " \
                    "WITH $fields as fields_batch, link1, link2 " \
                    "UNWIND fields_batch as field " \
                    "CREATE (link1)-[:ATTR]->(:Field {name: field.name, desc: field.desc, db: field.db, attrs: field.attrs, dbtype: field.dbtype}) " \
                    "RETURN link1.uuid as uuid;"


edit_link_info_query = "MATCH (hub1:Entity)-[hub1_main_rel:LINK]->(main_link: Link {uuid: $link_uuid})-[hub2_main_rel:LINK]->(hub2:Entity)-[hub2_paired_rel:LINK]-(paired_link:Link)-[hub1_paired_rel:LINK]->(hub1:Entity) " \
                       "SET main_link.desc=$main_link.desc, main_link.name=$main_link.name, main_link.db=$db " \
                       "SET paired_link.desc=$paired_link.desc, paired_link.name=$paired_link.name, paired_link.db=$db " \
                       "SET hub1_main_rel.on=[$main_link.ref_table_pk, $main_link.fk] " \
                       "SET hub2_main_rel.on=[$paired_link.fk, $paired_link.ref_table_pk] " \
                       "SET hub2_paired_rel.on=[$paired_link.ref_table_pk, $paired_link.fk] " \
                       "SET hub1_paired_rel.on=[$main_link.fk, $main_link.ref_table_pk] " \
                       "RETURN main_link.uuid as uuid;"


edit_main_hub_query = "MATCH (hub1:Entity)-[old_hub1_main_rel:LINK]->(main_link: Link {uuid: $link_uuid})-[hub2_main_rel:LINK]->(hub2:Entity)-[hub2_paired_rel:LINK]-(paired_link:Link)-[old_hub1_paired_rel:LINK]->(hub1:Entity) " \
                      "MATCH (new_main_hub:Entity {uuid: $main_link.ref_table_uuid}) " \
                      "CREATE (new_main_hub)-[:LINK {on: [$main_link.ref_table_pk, $main_link.fk]}]->(main_link) " \
                      "CREATE (paired_link)-[:LINK {on: [$main_link.fk, $main_link.ref_table_pk]}]->(new_main_hub) " \
                      "DELETE old_hub1_main_rel, old_hub1_paired_rel " \
                      "RETURN main_link.uuid as uuid;"


edit_paired_hub_query = "MATCH (hub1:Entity)-[hub1_main_rel:LINK]->(main_link: Link {uuid: $link_uuid})-[old_hub2_main_rel:LINK]->(hub2:Entity)-[old_hub2_paired_rel:LINK]-(paired_link:Link)-[hub1_paired_rel:LINK]->(hub1:Entity) " \
                        "MATCH (new_paired_hub:Entity {uuid: $paired_link.ref_table_uuid}) " \
                        "CREATE (new_paired_hub)-[:LINK {on: [$paired_link.ref_table_pk, $paired_link.fk]}]->(paired_link) " \
                        "CREATE (main_link)-[:LINK {on: [$paired_link.fk, $paired_link.ref_table_pk]}]->(new_paired_hub) " \
                        "DELETE old_hub2_main_rel, old_hub2_paired_rel " \
                        "RETURN main_link.uuid as uuid;"


edit_both_hubs_query = "MATCH (hub1:Entity)-[old_hub1_main_rel:LINK]->(main_link: Link {uuid: $link_uuid})-[old_hub2_main_rel:LINK]->(hub2:Entity)-[old_hub2_paired_rel:LINK]-(paired_link:Link)-[old_hub1_paired_rel:LINK]->(hub1:Entity) " \
                       "MATCH (new_main_hub:Entity {uuid: $main_link.ref_table_uuid}) " \
                       "MATCH (new_paired_hub:Entity {uuid: $paired_link.ref_table_uuid}) " \
                       "CREATE (new_main_hub)-[:LINK {on: [$main_link.ref_table_pk, $main_link.fk]}]->(main_link) " \
                       "CREATE (paired_link)-[:LINK {on: [$main_link.fk, $main_link.ref_table_pk]}]->(new_main_hub) " \
                       "CREATE (new_paired_hub)-[:LINK {on: [$paired_link.ref_table_pk, $paired_link.fk]}]->(paired_link) " \
                       "CREATE (main_link)-[:LINK {on: [$paired_link.fk, $paired_link.ref_table_pk]}]->(new_paired_hub) " \
                       "DELETE old_hub1_main_rel, old_hub1_paired_rel, old_hub2_main_rel, old_hub2_paired_rel " \
                       "RETURN main_link.uuid as uuid;"


delete_link_query = "MATCH (main_link:Link {uuid: $link_uuid}) " \
                    "MATCH (e1:Entity)-[:LINK]->(main_link)-[:LINK]->(e2:Entity)-[:LINK]->(paired_link:Link)-[:LINK]->(e1:Entity) " \
                    "OPTIONAL MATCH (main_link)-[:SAT]->(mls:Sat)-[:ATTR]->(mlsf:Field) " \
                    "OPTIONAL MATCH (paired_link)-[:SAT]->(pls:Sat)-[:ATTR]->(plsf:Field) " \
                    "OPTIONAL MATCH (main_link)-[:ATTR]->(mlf:Field) " \
                    "OPTIONAL MATCH (paired_link)-[:ATTR]->(plf:Field) " \
                    "WITH main_link.uuid as main_link_uuid, paired_link.uuid as paired_link_uuid, mls, mlsf, pls, plsf, mlf, plf, main_link, paired_link " \
                    "DETACH DELETE mls, mlsf, pls, plsf, mlf, plf, main_link, paired_link " \
                    "RETURN main_link_uuid, paired_link_uuid;"


check_on_hubs_query = "MATCH (hub1:Entity {uuid: $ref_table_uuid1 }) " \
                      "MATCH (hub2:Entity {uuid: $ref_table_uuid2 }) " \
                      "MATCH (hub1)-[:LINK]->(link1:Link)-[:LINK]->(hub2)-[:LINK]->(link2:Link)-[:LINK]->(hub1) " \
                      "RETURN hub1.name as hub1_name, hub2.name as hub2_name;"


check_on_nodes_existence_query = "UNWIND $nodes_uuids as node_uuid " \
                                 "MATCH (node {uuid: node_uuid}) " \
                                 "WHERE $type_ in labels(node) " \
                                 "RETURN count(node) as count;"
