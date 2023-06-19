"""resources

Revision ID: 3745083d4de3
Revises: 2ee335540c3e
Create Date: 2023-06-19 06:23:07.810281

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3745083d4de3'
down_revision = '2ee335540c3e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('model_data_types', 'additional')
    op.add_column('model_resource_attributes', sa.Column('additional', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.drop_column('model_resources', 'xml')
    op.drop_column('model_resources', 'json')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('model_resources', sa.Column('json', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('model_resources', sa.Column('xml', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_column('model_resource_attributes', 'additional')
    op.add_column('model_data_types', sa.Column('additional', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
