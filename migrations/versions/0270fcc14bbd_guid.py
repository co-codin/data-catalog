"""guid

Revision ID: 0270fcc14bbd
Revises: 7ee3c385109f
Create Date: 2023-05-25 10:49:33.579035

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0270fcc14bbd'
down_revision = '7ee3c385109f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('model_versions', sa.Column('guid', sa.String(length=36), nullable=False))
    op.create_index(op.f('ix_model_versions_guid'), 'model_versions', ['guid'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_model_versions_guid'), table_name='model_versions')
    op.drop_column('model_versions', 'guid')
    # ### end Alembic commands ###
