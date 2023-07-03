"""foreign_keys

Revision ID: a41df1f3e685
Revises: 5c9927192a4e
Create Date: 2023-07-03 06:49:19.958304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a41df1f3e685'
down_revision = '5c9927192a4e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('model_attitudes_resource_id_fkey', 'model_attitudes', type_='foreignkey')
    op.create_foreign_key(None, 'model_attitudes', 'model_resources', ['resource_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('model_qualities_model_version_id_fkey', 'model_qualities', type_='foreignkey')
    op.create_foreign_key(None, 'model_qualities', 'model_versions', ['model_version_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('model_relation_groups_model_version_id_fkey', 'model_relation_groups', type_='foreignkey')
    op.create_foreign_key(None, 'model_relation_groups', 'model_versions', ['model_version_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('model_relations_model_relation_group_id_fkey', 'model_relations', type_='foreignkey')
    op.create_foreign_key(None, 'model_relations', 'model_relation_groups', ['model_relation_group_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('model_resource_attributes_resource_id_fkey', 'model_resource_attributes', type_='foreignkey')
    op.create_foreign_key(None, 'model_resource_attributes', 'model_resources', ['resource_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('model_resources_model_version_id_fkey', 'model_resources', type_='foreignkey')
    op.create_foreign_key(None, 'model_resources', 'model_versions', ['model_version_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'model_resources', type_='foreignkey')
    op.create_foreign_key('model_resources_model_version_id_fkey', 'model_resources', 'model_versions', ['model_version_id'], ['id'])
    op.drop_constraint(None, 'model_resource_attributes', type_='foreignkey')
    op.create_foreign_key('model_resource_attributes_resource_id_fkey', 'model_resource_attributes', 'model_resources', ['resource_id'], ['id'])
    op.drop_constraint(None, 'model_relations', type_='foreignkey')
    op.create_foreign_key('model_relations_model_relation_group_id_fkey', 'model_relations', 'model_relation_groups', ['model_relation_group_id'], ['id'])
    op.drop_constraint(None, 'model_relation_groups', type_='foreignkey')
    op.create_foreign_key('model_relation_groups_model_version_id_fkey', 'model_relation_groups', 'model_versions', ['model_version_id'], ['id'])
    op.drop_constraint(None, 'model_qualities', type_='foreignkey')
    op.create_foreign_key('model_qualities_model_version_id_fkey', 'model_qualities', 'model_versions', ['model_version_id'], ['id'])
    op.drop_constraint(None, 'model_attitudes', type_='foreignkey')
    op.create_foreign_key('model_attitudes_resource_id_fkey', 'model_attitudes', 'model_resources', ['resource_id'], ['id'])
    # ### end Alembic commands ###
