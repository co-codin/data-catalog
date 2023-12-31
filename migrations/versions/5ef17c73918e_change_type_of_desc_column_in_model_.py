"""change type of desc column in model_resources table

Revision ID: 5ef17c73918e
Revises: 38c3d0f43b81
Create Date: 2023-06-23 15:37:17.296859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ef17c73918e'
down_revision = '38c3d0f43b81'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('model_versions', 'desc',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.Text(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('model_versions', 'desc',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=100),
               existing_nullable=True)
    # ### end Alembic commands ###
