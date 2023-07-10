import asyncio
import uuid

from datetime import datetime

from fastapi import HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, desc
from sqlalchemy.orm import selectinload, joinedload

from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.crud.crud_tag import add_tags, update_tags
from app.enums.enums import ModelVersionLevel, ModelVersionStatus
from app.errors.checker import check_model_resources_error
from app.models.models import ModelVersion, ModelQuality, ModelAttitude, ModelResource, ModelResourceAttribute, \
    ModelRelation
from app.schemas.model_resource import ModelResourceOutRelIn
from app.schemas.model_version import ModelVersionIn, ModelVersionUpdateIn, ModelVersionOut


async def generate_version_number(id: int, session: AsyncSession, level: ModelVersionLevel):
    model_version = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.id == id)
    )
    model_version = model_version.scalars().first()

    if model_version.status != ModelVersionStatus.ARCHIVE.value \
            and model_version.status != ModelVersionStatus.APPROVED.value:
        if model_version.version is None:
            critical = 0
            minor = 0
            patch = 0
        else:
            version = model_version.version.split('.')
            critical = int(version[0])
            minor = int(version[1])
            patch = int(version[2])

        match level:
            case ModelVersionLevel.CRITICAL:
                critical = critical + 1
                minor = 0
                patch = 0
            case ModelVersionLevel.MINOR:
                minor = minor + 1
                patch = 0
            case ModelVersionLevel.PATCH:
                patch = patch + 1

        await session.execute(
            update(ModelVersion)
            .where(ModelVersion.id == id)
            .values(
                version=str(critical) + "." + str(minor) + "." + str(patch)
            )
        )


async def read_all(model_id: str, session: AsyncSession):
    await generate_version_number(id=1, session=session, level=ModelVersionLevel.PATCH)
    model_versions = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.model_id == model_id)
        .options(selectinload(ModelVersion.comments))
    )
    model_versions = model_versions.scalars().all()
    return model_versions


async def update_model_version(guid: str, model_version_update_in: ModelVersionUpdateIn, session: AsyncSession):
    model_version = await session.execute(
        select(ModelVersion)
        .options(selectinload(ModelVersion.tags))
        .options(joinedload(ModelVersion.model_resources).selectinload(ModelResource.attributes))
        .filter(ModelVersion.guid == guid)
    )
    model_version = model_version.scalars().first()
    await check_model_resources_error(model_version=model_version, status_in=model_version_update_in.status,
                                      session=session)

    approved_model_version = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.model_id == model_version.model_id)
        .filter(ModelVersion.status == ModelVersionStatus.APPROVED.value)
        .order_by(ModelVersion.id)
    )
    approved_model_version = approved_model_version.scalars().first()

    if not model_version.status == ModelVersionStatus.DRAFT.value:
        model_version_update_in.status = model_version.status
    elif model_version.status == ModelVersionStatus.DRAFT.value and approved_model_version \
            and model_version_update_in.status == ModelVersionStatus.APPROVED.value:
        approved_model_version.status = ModelVersionStatus.ARCHIVE.value
        model_version.confirmed_at = datetime.now()

    model_version_update_in_data = {
        key: value for key, value in model_version_update_in.dict(exclude={'tags'}).items()
        if value is not None
    }

    if model_version.status == ModelVersionStatus.DRAFT.value and not model_version.version:
        model_version_update_in_data['version'] = str(uuid.uuid4())

    await session.execute(
        update(ModelVersion)
        .where(ModelVersion.guid == guid)
        .values(
            **model_version_update_in_data,
        )
    )

    await update_tags(model_version, session, model_version_update_in.tags)

    session.add(model_version)
    await session.commit()


async def read_by_guid(guid: str, token: str, session: AsyncSession) -> ModelVersionOut:
    model_version = await session.execute(
        select(ModelVersion)
        .options(selectinload(ModelVersion.tags))
        .options(selectinload(ModelVersion.comments))
        .options(selectinload(ModelVersion.model_qualities).selectinload(ModelQuality.tags))
        .options(selectinload(ModelVersion.model_qualities).selectinload(ModelQuality.comments))
        .filter(ModelVersion.guid == guid)
    )
    model_version = model_version.scalars().first()

    if not model_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    model_version_out = ModelVersionOut.from_orm(model_version)

    if model_version.comments:
        author_guids = {comment.author_guid for comment in model_version.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, get_authors_data_by_guids, author_guids, token
        )
        set_author_data(model_version_out.comments, authors_data)

    return model_version_out


async def delete_model_version(guid: str, session: AsyncSession):
    model_version = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.guid == guid)
    )
    model_version = model_version.scalars().first()

    if not model_version.status == ModelVersionStatus.DRAFT.value:
        raise HTTPException(status_code=403, detail='Можно удалить только черновика')

    await session.execute(
        delete(ModelVersion)
        .where(ModelVersion.guid == guid)
    )
    await session.commit()


async def clone_attitudes(old_version_id: int, session: AsyncSession, model_attributes_mapping: [int],
                          model_resources_mapping: [int]):
    model_attitudes = await session.execute(
        select(ModelAttitude)
        .filter(ModelResource.model_version_id == old_version_id)
    )
    model_attitudes = model_attitudes.scalars().all()
    for exists_model_attitude in model_attitudes:
        left_attribute_id = exists_model_attitude.left_attribute_id
        if left_attribute_id in model_attributes_mapping:
            left_attribute_id = model_attributes_mapping[left_attribute_id]

        right_attribute_id = exists_model_attitude.right_attribute_id
        if right_attribute_id in model_attributes_mapping:
            right_attribute_id = model_attributes_mapping[right_attribute_id]

        resource_id = exists_model_attitude.resource_id
        if exists_model_attitude.resource_id in model_resources_mapping:
            resource_id = model_resources_mapping[exists_model_attitude.resource_id]
        model_attitude = ModelAttitude(
            resource_id=resource_id,
            guid=str(uuid.uuid4()),
            left_attribute_id=left_attribute_id,
            right_attribute_id=right_attribute_id
        )
        session.add(model_attitude)


async def clone_attributes(old_resource_id: int, new_resource_id: int, session: AsyncSession,
                           model_attributes_mapping: {}) -> {}:
    model_attributes = await session.execute(
        select(ModelResourceAttribute)
        .options(selectinload(ModelResourceAttribute.tags))
        .filter(ModelResourceAttribute.resource_id == old_resource_id)
    )
    model_attributes = model_attributes.scalars().all()
    for exists_model_resource_attribute in model_attributes:
        model_attribute = ModelResourceAttribute(
            name=exists_model_resource_attribute.name,
            key=exists_model_resource_attribute.key,
            db_link=exists_model_resource_attribute.db_link,
            desc=exists_model_resource_attribute.desc,
            resource_id=new_resource_id,
            model_resource_id=exists_model_resource_attribute.model_resource_id,
            model_data_type_id=exists_model_resource_attribute.model_data_type_id,
            cardinality=exists_model_resource_attribute.cardinality,
            parent_id=exists_model_resource_attribute.parent_id,
            additional=exists_model_resource_attribute.additional,
            guid=str(uuid.uuid4())
        )

        tags = []
        for tag in exists_model_resource_attribute.tags:
            tags.append(tag.name)
        await add_tags(model_attribute, tags, session)
        session.add(model_attribute)
        await session.commit()

        model_attributes_mapping[exists_model_resource_attribute.id] = model_attribute.id

    return model_attributes_mapping


async def clone_attribute_relations(new_version_id: int, session: AsyncSession, model_attributes_mapping: {},
                                    model_resources_mapping: {}):
    model_resources = await session.execute(
        select(ModelResource)
        .options(selectinload(ModelResource.tags))
        .filter(ModelResource.model_version_id == new_version_id)
    )
    model_resources = model_resources.scalars().all()
    for model_resource in model_resources:
        model_attributes = await session.execute(
            select(ModelResourceAttribute)
            .options(selectinload(ModelResourceAttribute.tags))
            .filter(ModelResourceAttribute.resource_id == model_resource.id)
        )
        model_attributes = model_attributes.scalars().all()

        for model_attribute in model_attributes:
            if model_attribute.parent_id is None:
                parent_id = None
            else:
                parent_id = model_attributes_mapping[model_attribute.parent_id]
            if model_attribute.model_resource_id is None:
                model_resource_id = None
            else:
                model_resource_id = model_resources_mapping[model_attribute.model_resource_id]
            await session.execute(
                update(ModelResourceAttribute)
                .where(ModelResourceAttribute.guid == model_attribute.guid)
                .values(
                    model_resource_id=model_resource_id,
                    parent_id=parent_id
                )
            )


async def clone_resources(old_version_id: int, new_version_id: int, session: AsyncSession):
    model_resources = await session.execute(
        select(ModelResource)
        .options(selectinload(ModelResource.tags))
        .filter(ModelResource.model_version_id == old_version_id)
    )
    model_resources = model_resources.scalars().all()
    model_resources_mapping = {}
    model_attributes_mapping = {}
    for exists_model_resource in model_resources:
        model_resource = ModelResource(
            model_version_id=new_version_id,
            name=exists_model_resource.name,
            owner=exists_model_resource.owner,
            desc=exists_model_resource.desc,
            type=exists_model_resource.type,
            db_link=exists_model_resource.db_link,
            json=exists_model_resource.json,
            xml=exists_model_resource.xml,
            guid=str(uuid.uuid4())
        )

        tags = []
        for tag in exists_model_resource.tags:
            tags.append(tag.name)
        await add_tags(model_resource, tags, session)
        session.add(model_resource)
        await session.commit()

        model_resources_mapping[exists_model_resource.id] = model_resource.id
        model_attributes_mapping = await clone_attributes(old_resource_id=exists_model_resource.id,
                                                          new_resource_id=model_resource.id, session=session,
                                                          model_attributes_mapping=model_attributes_mapping)

    return model_resources_mapping, model_attributes_mapping


async def clone_relations(old_version_id: int, new_version_id: int, session: AsyncSession):
    exists_model_relations = await session.execute(
        select(ModelRelation)
        .options(selectinload(ModelRelation.tags))
        .filter(ModelRelation.model_version_id == old_version_id)
    )
    model_relations = exists_model_relations.scalars().all()
    for exists_model_relation in model_relations:
        model_relation = ModelRelation(
            model_version_id=new_version_id,
            name=exists_model_relation.name,
            owner=exists_model_relation.owner,
            desc=exists_model_relation.desc,
            operation_id=exists_model_relation.operation_id,
            guid=str(uuid.uuid4())
        )

        tags = []
        for tag in exists_model_relation.tags:
            tags.append(tag.name)
        await add_tags(model_relation, tags, session)
        session.add(model_relation)
        await session.commit()


async def clone_qualities(old_version_id: int, new_version_id: int, session: AsyncSession):
    model_qualities = await session.execute(
        select(ModelQuality)
        .options(selectinload(ModelQuality.tags))
        .where(ModelQuality.model_version_id == old_version_id)
    )
    model_qualities = model_qualities.scalars().all()
    for exists_model_quality in model_qualities:
        model_quality = ModelQuality(
            model_version_id=new_version_id,
            name=exists_model_quality.name,
            owner=exists_model_quality.owner,
            desc=exists_model_quality.desc,
            function=exists_model_quality.function,
            guid=str(uuid.uuid4())
        )

        tags = []
        for tag in exists_model_quality.tags:
            tags.append(tag.name)
        await add_tags(model_quality, tags, session)
        session.add(model_quality)


async def create_model_version(model_version_in: ModelVersionIn, session: AsyncSession) -> ModelVersion:
    guid = str(uuid.uuid4())
    model_version = ModelVersion(
        **model_version_in.dict(exclude={'tags'}),
        guid=guid
    )

    await add_tags(model_version, model_version_in.tags, session)
    session.add(model_version)
    await session.commit()

    await clone_model_version(model_version=model_version, model_version_in=model_version_in, session=session)
    return model_version


async def clone_model_version(model_version: ModelVersion, model_version_in: ModelVersionIn,
                              session: AsyncSession) -> bool:
    count_model_versions_draft = await session.execute(
        select(func.count(ModelVersion.id))
        .where(ModelVersion.status == "draft")
        .filter(ModelVersion.model_id == model_version_in.model_id)
    )
    count_model_versions_draft = count_model_versions_draft.scalars().first()

    if count_model_versions_draft == 1:
        last_approved_model_version = await session.execute(
            select(ModelVersion)
            .options(selectinload(ModelVersion.tags))
            .filter(and_(ModelVersion.model_id == model_version_in.model_id, ModelVersion.status == "approved"))
            .order_by(desc(ModelVersion.updated_at))
        )
        last_approved_model_version = last_approved_model_version.scalars().first()
        if last_approved_model_version is not None:
            await clone_qualities(old_version_id=last_approved_model_version.id, new_version_id=model_version.id,
                                  session=session)
            await clone_relations(old_version_id=last_approved_model_version.id, new_version_id=model_version.id,
                                  session=session)
            model_resources_mapping, model_attributes_mapping = await clone_resources(
                old_version_id=last_approved_model_version.id, new_version_id=model_version.id, session=session)

            await clone_attribute_relations(new_version_id=model_version.id, session=session,
                                            model_attributes_mapping=model_attributes_mapping,
                                            model_resources_mapping=model_resources_mapping)

            await clone_attitudes(old_version_id=last_approved_model_version.id, session=session,
                                  model_attributes_mapping=model_attributes_mapping,
                                  model_resources_mapping=model_resources_mapping)

            await session.execute(
                update(ModelVersion)
                .where(ModelVersion.guid == model_version.guid)
                .values(
                    desc=last_approved_model_version.desc,
                    version=None
                )
            )

            tags = model_version_in.tags
            for tag in last_approved_model_version.tags:
                tags.append(tag.name)
            if tags:
                model_version = await session.execute(
                    select(ModelVersion)
                    .options(selectinload(ModelVersion.tags))
                    .options(selectinload(ModelVersion.comments))
                    .options(selectinload(ModelVersion.model_qualities).selectinload(ModelQuality.tags))
                    .options(selectinload(ModelVersion.model_qualities).selectinload(ModelQuality.comments))
                    .filter(ModelVersion.guid == model_version.guid)
                )
                model_version = model_version.scalars().first()
                await update_tags(model_version, session, tags)

            return True
    return False


async def read_resources(guid: str, session: AsyncSession) -> list[ModelResourceOutRelIn]:
    model_version = await session.execute(
        select(ModelVersion)
        .options(selectinload(ModelVersion.model_resources))
        .where(ModelVersion.guid == guid)
    )
    model_version = model_version.scalars().first()
    if not model_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return [
        ModelResourceOutRelIn.from_orm(resource)
        for resource in model_version.model_resources
    ]
