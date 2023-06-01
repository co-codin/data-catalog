"""Mark id as UID

Revision ID: e818726ca4df
Revises: 8b51cc56ef77
Create Date: 2023-05-31 14:45:59.366612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e818726ca4df'
down_revision = '8b51cc56ef77'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('model_qualities', sa.Column('guid', sa.String(length=36), nullable=False))
    op.create_index(op.f('ix_model_qualities_guid'), 'model_qualities', ['guid'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_model_qualities_guid'), table_name='model_qualities')
    op.drop_column('model_qualities', 'guid')
    # ### end Alembic commands ###
