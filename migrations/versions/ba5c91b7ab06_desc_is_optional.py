"""desc is optional

Revision ID: ba5c91b7ab06
Revises: 5ef17c73918e
Create Date: 2023-06-23 17:00:15.332889

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba5c91b7ab06'
down_revision = '5ef17c73918e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('model_resource_attributes', 'desc',
               existing_type=sa.TEXT(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('model_resource_attributes', 'desc',
               existing_type=sa.TEXT(),
               nullable=False)
    # ### end Alembic commands ###
