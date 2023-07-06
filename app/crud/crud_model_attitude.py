# import uuid
#
# from sqlalchemy import select, delete, func, or_
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import load_only
#
# from fastapi import status, HTTPException
#
# from age import Age
#
# from app.crud.crud_model_version import generate_version_number, VersionLevel
# from app.errors.errors import ModelAttitudeAttributesError
# from app.models.models import ModelAttitude, ModelResourceAttribute, ModelResource
# from app.schemas.model_attitude import ModelAttitudeIn, ModelResourceRelOut, ModelResourceRelIn
# from app.age_queries.node_queries import match_model_resource_rels, set_link_between_nodes
#
#
# async def read_attitudes_by_resource_id(
#         resource_id: int, session: AsyncSession, age_session: Age
# ) -> list[ModelResourceRelOut]:
#     model_resource = await session.execute(
#         select(ModelResource)
#         .options(load_only(ModelResource.name, ModelResource.db_link))
#         .where(ModelResource.id == resource_id)
#     )
#     model_resource = model_resource.scalars().first()
#     if not model_resource:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="model resource doesn't exist")
#
#     graph_name = model_resource.db_link.rsplit('.', maxsplit=1)[0]
#     age_session.setGraph(graph_name)
#     cursor = age_session.execCypher(
#         match_model_resource_rels, cols=['rel', 't2_name'], params=(model_resource.name,)
#     )
#     return [
#         ModelResourceRelOut(
#             resource_attr=model_resource_rel[0][1], mapped_resource=model_resource_rel[1],
#             key_attr=model_resource_rel[0][0]
#         )
#         for model_resource_rel in cursor
#     ]
#
#
# async def create_model_attitude(
#         attitude_in: ModelResourceRelIn, session: AsyncSession, age_session: Age
# ) -> None:
#     mapped_model_resource = await session.execute(
#         select(ModelResource)
#         .where(ModelResource.guid == attitude_in.mapped_resource_guid)
#     )
#     mapped_model_resource = mapped_model_resource.scalars().all()
#     if not mapped_model_resource:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
#
#     graph_name = mapped_model_resource.db_link.rsplit('.', maxsplit=1)[0]
#     age_session.setGraph(graph_name)
#     # set link between two nodes
#     age_session.execCypher(set_link_between_nodes, params=())
#
#     await generate_version_number(id=mapped_model_resource.model_version_id, session=session, level=VersionLevel.MINOR)
#
#
# async def delete_model_attitude(guid: str, session: AsyncSession):
#     model_attitude = await session.execute(
#         select(ModelAttitude)
#         .filter(ModelAttitude.guid == guid)
#     )
#     model_attitude = model_attitude.scalars().all()
#
#     model_resource = await session.execute(
#         delete(ModelResource)
#         .where(ModelResource.guid == model_attitude.left_attribute_id)
#     )
#     model_resource = model_resource.scalars().first()
#     await generate_version_number(id=model_resource.model_version_id, session=session, level=VersionLevel.MINOR)
#
#     await session.execute(
#         delete(ModelAttitude)
#         .where(ModelAttitude.guid == guid)
#     )
#     await session.commit()
