import asyncio
import uuid

from sqlalchemy import select, update, delete, func, Identity
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.crud.crud_author import get_authors_data_by_guids, set_author_data
from app.crud.crud_tag import add_tags, update_tags
from app.enums.enums import ModelVersionStatus, PipelineStatus
from app.errors.pipeline_errors import ModelVersionStatusError, PipelineNameNotUniqueError
from app.models import Pipeline, ModelVersion, Model, PipelineResult
from app.schemas.pipeline import PipelineIn, PipelineUpdateIn


async def create_pipeline(pipeline_in: PipelineIn, session: AsyncSession, author_guid: str) -> Pipeline:
    guid = str(uuid.uuid4())

    model_version = await session.execute(
        select(ModelVersion)
        .filter(ModelVersion.id == pipeline_in.model_version_id)
    )
    model_version = model_version.scalars().first()

    if model_version.status != ModelVersionStatus.APPROVED.value \
            and model_version.status != ModelVersionStatus.ARCHIVE.value:
        raise ModelVersionStatusError()

    if pipeline_in.name is None:
        model = await session.execute(
            select(Model)
            .filter(Model.id == model_version.model_id)
        )
        model = model.scalars().first()

        if pipeline_in.base:
            base = "Критерии Качества"
        else:
            base = "Связи"

        if pipeline_in.operating_mode:
            mode = "Apache NiFi"
        else:
            mode = "Apache Airflow"

        pipeline_in.name = model.name + " " + str(model_version.version) + " " + base + " " + mode

    if pipeline_in.owner is None:
        pipeline_in.owner = author_guid

    pipeline_count = await session.execute(
        select(func.count(Pipeline.id))
        .filter(Pipeline.name == pipeline_in.name)
    )
    pipeline_count = pipeline_count.scalars().first()
    if pipeline_count != 0:
        raise PipelineNameNotUniqueError()

    pipeline = Pipeline(
        **pipeline_in.dict(exclude={'tags'}),
        guid=guid
    )

    await add_tags(pipeline, pipeline_in.tags, session)
    session.add(pipeline)

    await session.commit()
    return pipeline


async def read_all(session: AsyncSession):
    pipelines = await session.execute(
        select(Pipeline)
        .options(selectinload(Pipeline.comments))
    )
    pipelines = pipelines.scalars().all()
    return pipelines


async def read_by_guid(guid: str, token: str, session: AsyncSession):
    pipeline = await session.execute(
        select(Pipeline)
        .options(selectinload(Pipeline.tags))
        .options(selectinload(Pipeline.comments))
        .filter(Pipeline.guid == guid)
    )
    pipeline = pipeline.scalars().first()

    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if pipeline.comments:
        author_guids = {comment.author_guid for comment in pipeline.comments}
        authors_data = await asyncio.get_running_loop().run_in_executor(
            None, get_authors_data_by_guids, author_guids, token
        )
        set_author_data(pipeline.comments, authors_data)

    return pipeline


async def clone_instead_change(pipeline: Pipeline, pipeline_update_in: PipelineUpdateIn, session: AsyncSession,
                               author_guid: str):
    if pipeline_update_in.model_version_id is not None or pipeline_update_in.operating_mode is not None \
            or pipeline_update_in.base is not None:

        if pipeline_update_in.owner is None:
            owner = pipeline.owner
        else:
            owner = pipeline_update_in.owner

        if pipeline_update_in.desc is None:
            desc = pipeline.desc
        else:
            desc = pipeline_update_in.desc

        if pipeline_update_in.operating_mode is None:
            operating_mode = pipeline.operating_mode
        else:
            operating_mode = pipeline_update_in.operating_mode

        if pipeline_update_in.model_version_id is None:
            model_version_id = pipeline.model_version_id
        else:
            model_version_id = pipeline_update_in.model_version_id

        if pipeline_update_in.state is None:
            state = pipeline.state
        else:
            state = pipeline_update_in.state

        if pipeline_update_in.base is None:
            base = pipeline.base
        else:
            base = pipeline_update_in.base

        tags = []
        for tag in pipeline.tags:
            tags.append(tag.name)
        if pipeline_update_in.tags is not None:
            tags = tags + pipeline_update_in.tags

        pipeline_in = PipelineIn(
            owner=owner,
            desc=desc,
            operating_mode=operating_mode,
            model_version_id=model_version_id,
            state=state,
            base=base,
            tags=tags
        )

        pipeline = await create_pipeline(pipeline_in=pipeline_in, session=session, author_guid=author_guid)
        return True, pipeline
    return False, None


async def update_pipeline(guid: str, pipeline_update_in: PipelineUpdateIn, session: AsyncSession, user: Identity):
    pipeline = await session.execute(
        select(Pipeline)
        .options(selectinload(Pipeline.tags))
        .filter(Pipeline.guid == guid)
    )
    pipeline = pipeline.scalars().first()

    cloned, new_pipeline = await clone_instead_change(pipeline=pipeline, pipeline_update_in=pipeline_update_in, session=session,
                                      author_guid=user['identity_id'])

    if cloned:
        return new_pipeline
    else:
        pipeline_update_in_data = {
            key: value for key, value in pipeline_update_in.dict(exclude={'tags'}).items()
            if value is not None
        }

        await session.execute(
            update(Pipeline)
            .where(Pipeline.guid == guid)
            .values(
                **pipeline_update_in_data,
            )
        )

        await update_tags(pipeline, session, pipeline_update_in.tags)
        return pipeline


async def delete_pipeline(guid: str, session: AsyncSession):
    await session.execute(
        delete(Pipeline)
        .where(Pipeline.guid == guid)
    )


async def generate_pipeline(pipeline_id: int, session: AsyncSession):
    pipeline_result = await session.execute(
        select(PipelineResult)
        .filter(PipelineResult.pipeline_id == pipeline_id)
    )
    pipeline_result = pipeline_result.scalars().first()
    if pipeline_result is None:
        pipeline_result = PipelineResult(
            pipeline_id=pipeline_id,
        )
        session.add(pipeline_result)
        await session.commit()
    else:
        await session.execute(
            update(PipelineResult)
            .where(Pipeline.guid == pipeline_id)
            .values(
                status=PipelineStatus.EXPECTED.value,
                attachment=None
            )
        )
