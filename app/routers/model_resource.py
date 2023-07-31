import asyncio

from fastapi import APIRouter, Depends, Query

from app.crud.crud_model_resource import (
    read_resources_by_version_id, read_resources_by_guid, create_model_resource,
    update_model_resource, delete_model_resource, create_attribute, edit_attribute, remove_attribute,
    get_attribute_by_guid, read_model_resource_attrs, read_model_resource_rels, create_model_resource_rel,
    check_on_model_resources_len, remove_model_resource_rel, read_model_resource
)

from app.crud.crud_comment import CommentOwnerTypes, create_comment, edit_comment, remove_comment, verify_comment_owner
from app.crud.crud_model_version import generate_version_number
from app.crud.crud_queries import select_model_resource, match_linked_resources, select_all_resources, \
    filter_connected_resources
from app.enums.enums import ModelVersionLevel
from app.errors.errors import ModelResourceHasAttributesError
from app.schemas.model_resource_rel import ModelResourceRelIn, ModelResourceRelOut

from app.schemas.model_attribute import ResourceAttributeIn, ResourceAttributeUpdateIn, ModelResourceAttrOutRelIn
from app.schemas.model_resource import ModelResourceIn, ModelResourceUpdateIn
from app.schemas.queries import ModelResourceOut
from app.schemas.source_registry import CommentIn

from app.dependencies import db_session, get_user, get_token, ag_session

router = APIRouter(
    prefix="/model_resource",
    tags=['model resource']
)


@router.get('/by_version/{version_id}')
async def get_model_resources(version_id: int, session=Depends(db_session), _=Depends(get_user)):
    return await read_resources_by_version_id(version_id, session)


@router.get('/{guid}')
async def get_model_resource(guid: str, session=Depends(db_session), token=Depends(get_token)):
    return await read_resources_by_guid(guid, token, session)


@router.post('/')
async def add_model_resource(resource_in: ModelResourceIn, session=Depends(db_session), _=Depends(get_user)):
    guid = await create_model_resource(resource_in, session)

    return {'guid': guid}


@router.put('/{guid}')
async def update(guid: str, resource_update_in: ModelResourceUpdateIn, session=Depends(db_session),
                 _=Depends(get_user)):
    return await update_model_resource(guid, resource_update_in, session)


@router.delete('/{guid}')
async def delete(guid: str, session=Depends(db_session), _=Depends(get_user)):
    try:
        return await delete_model_resource(guid, session)
    except:
        raise ModelResourceHasAttributesError()


@router.post('/{guid}/comments')
async def add_comment(guid: str, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    comment_id = await create_comment(guid, user['identity_id'], comment, CommentOwnerTypes.model_resource, session)
    return {'id': comment_id}


@router.put('/comments/{id_}')
async def update_comment(id_: int, comment: CommentIn, session=Depends(db_session), user=Depends(get_user)):
    await verify_comment_owner(id_, user['identity_id'], session)
    await edit_comment(id_, comment, session)
    return {'msg': 'comment has been updated'}


@router.delete('/comments/{id_}')
async def delete_comment(id_: int, session=Depends(db_session), user=Depends(get_user)):
    await verify_comment_owner(id_, user['identity_id'], session)
    await remove_comment(id_, session)
    return {'msg': 'comment has been deleted'}


@router.post('/attributes')
async def add_attribute(attribute_in: ResourceAttributeIn, session=Depends(db_session)):
    resource_attribute_guid = await create_attribute(attribute_in, session)
    return {'guid': resource_attribute_guid}


@router.get('/attributes/{guid}')
async def get_attribute(guid: str, session=Depends(db_session)):
    return await get_attribute_by_guid(guid, session)


@router.put('/attributes/{guid}')
async def update_attribute(guid: str, attribute_update_in: ResourceAttributeUpdateIn, session=Depends(db_session)):
    await edit_attribute(guid, attribute_update_in, session)
    return {'msg': 'attribute has been updated'}


@router.delete('/attributes/{guid}')
async def delete_attribute(guid: str, session=Depends(db_session)):
    await remove_attribute(guid, session)
    return {'msg': 'attribute has been deleted'}


@router.get('/{guid}/attributes', response_model=list[ModelResourceAttrOutRelIn])
async def get_model_attrs(guid: str, session=Depends(db_session), _=Depends(get_user)):
    return await read_model_resource_attrs(guid, session)


@router.post('/{guid}/rels', response_model=int)
async def add_model_resource_rel(
        guid: str, rel_in: ModelResourceRelIn, session=Depends(db_session), age_session=Depends(ag_session),
        _=Depends(get_user)
):
    await check_on_model_resources_len(guid, rel_in.mapped_resource_guid, session)
    one_to_many_rel_id, model_version_id = await create_model_resource_rel(guid, rel_in, session, age_session)
    await generate_version_number(id=model_version_id, session=session, level=ModelVersionLevel.MINOR)
    return one_to_many_rel_id


@router.get('/{guid}/rels', response_model=list[ModelResourceRelOut])
async def get_model_resource_rels(
        guid: str, session=Depends(db_session), age_session=Depends(ag_session), _=Depends(get_user)
):
    return await read_model_resource_rels(guid, session, age_session)


@router.delete('/{guid}/rels/{gid}')
async def delete_model_resource_rels(
        guid: str, gid: int, session=Depends(db_session), age_session=Depends(ag_session), _=Depends(get_user)
):
    model_resource = await read_model_resource(guid, session)
    graph_name = model_resource.db_link.rsplit('.', maxsplit=1)[0]
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, remove_model_resource_rel, gid, graph_name, age_session)
    await generate_version_number(id=model_resource.model_version_id, session=session, level=ModelVersionLevel.MINOR)




@router.get('/{guid}/linked_resources', response_model=list[ModelResourceOut])
async def get_linked_resources(
        guid: str, model_version_id: int = Query(gt=0),
        session=Depends(db_session), age_session=Depends(ag_session), _=Depends(get_user)
):
    """
    1) select model resource attributes db links from db
    2) take graph_name from db_link field
    3) take resource names from db_link field
    4) set required graph
    5) match all directly connected tables with the ones from step 3
    6) filter them with model version id and db_link field
    """
    model_resource = await select_model_resource(guid, session)
    if not model_resource:
        return await select_all_resources(model_version_id, session)

    db, ns, resource_name = model_resource.db_link.split('.')
    graph_name = f'{db}.{ns}'

    loop = asyncio.get_running_loop()
    connected_resources = await loop.run_in_executor(
        None, match_linked_resources, resource_name, graph_name, age_session
    )
    connected_db_links = [f'{graph_name}.{connected_resource}' for connected_resource in connected_resources]
    model_resources = await filter_connected_resources(
        connected_db_links, model_version_id, session
    )
    return model_resources
