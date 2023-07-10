"""db_link indexes

Revision ID: affdf30945a3
Revises: 7e10e8ac9384
Create Date: 2023-07-10 07:09:36.067006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'affdf30945a3'
down_revision = '7e10e8ac9384'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_model_resource_attributes_db_link'), 'model_resource_attributes', ['db_link'], unique=False)
    op.create_index(op.f('ix_model_resource_attributes_parent_id'), 'model_resource_attributes', ['parent_id'], unique=False)
    op.create_index(op.f('ix_model_resources_db_link'), 'model_resources', ['db_link'], unique=False)
    op.create_index(op.f('ix_objects_db_path'), 'objects', ['db_path'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_objects_db_path'), table_name='objects')
    op.drop_index(op.f('ix_model_resources_db_link'), table_name='model_resources')
    op.drop_index(op.f('ix_model_resource_attributes_parent_id'), table_name='model_resource_attributes')
    op.drop_index(op.f('ix_model_resource_attributes_db_link'), table_name='model_resource_attributes')
    # ### end Alembic commands ###
