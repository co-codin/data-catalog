from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.enums import AccessLabelType
from app.models import Model, ModelVersion, ModelResource, ModelResourceAttribute
from app.models.access_label import AccessLabel
from app.schemas.access_label import AccessLabelIn


async def add_access_label(access_label_like_model: Model | ModelVersion | ModelResource | ModelResourceAttribute,
                           access_label_in: AccessLabelIn | ModelResource | ModelResourceAttribute | None):
    if not access_label_in:
        return

    if access_label_in.type == AccessLabelType.PERSONAL.value:
        access_label = AccessLabel(type=access_label_in.type, operation_version_id=access_label_in.operation_version_id)
        access_label_like_model.access_label.extend([access_label])
    elif access_label_in.type == AccessLabelType.CONFIDENTIAL.value:
        access_label = AccessLabel(type=access_label_in.type)
        access_label_like_model.access_label.extend([access_label])


async def update_access_label(access_label_like_model: Model | ModelVersion | ModelResource | ModelResourceAttribute,
                              access_label_update_in: AccessLabelIn | None,
                              session: AsyncSession):
    if not access_label_update_in:
        return

    exists_labels = [access_label.id for access_label in access_label_like_model.access_label]
    access_label_like_model.access_label[:] = []
    if exists_labels:
        await session.execute(
            delete(AccessLabel)
            .filter(AccessLabel.id.in_(exists_labels))
        )

    if access_label_update_in.type != AccessLabelType.FREE.value:
        await add_access_label(access_label_like_model, access_label_update_in)
