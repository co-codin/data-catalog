# from fastapi import APIRouter, Depends
#
# from app.dependencies import db_session, get_user, ag_session
# from app.crud.crud_model_attitude import read_attitudes_by_resource_id, create_model_attitude, delete_model_attitude
# from app.schemas.model_attitude import ModelResourceRelOut, ModelResourceRelIn
#
# router = APIRouter(
#     prefix="/model_resource_attitude",
#     tags=['model resource attitude']
# )
#
#
# @router.get('/by_resource/{resource_id}')
# async def get_model_attitudes(
#         resource_id: int, session=Depends(db_session), age_session=Depends(ag_session), user=Depends(get_user)
# ):
#     return await read_attitudes_by_resource_id(resource_id, session, age_session)
#
#
# @router.post('/')
# async def add_model_resource_attitude(
#         attitude_in: ModelResourceRelIn, session=Depends(db_session), age_session=Depends(ag_session),
#         user=Depends(get_user)
# ):
#     guid = await create_model_attitude(attitude_in, session, age_session)
#
#     return {'guid': guid}
#
#
# @router.delete('/{guid}')
# async def delete(guid: str, session=Depends(db_session), user=Depends(get_user)):
#     return await delete_model_attitude(guid, session)
