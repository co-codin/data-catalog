"""newest opration

Revision ID: 8a1ba1059dd1
Revises: d86fb15ef56b
Create Date: 2023-07-10 12:54:54.921185

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a1ba1059dd1'
down_revision = 'd86fb15ef56b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('model_resource_attributes', sa.Column('access_flag', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('model_resource_attributes', 'access_flag')
    # ### end Alembic commands ###
