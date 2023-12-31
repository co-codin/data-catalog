"""Change model data types

Revision ID: 7f2c3361d2bb
Revises: 899d03d2910a
Create Date: 2023-06-06 13:24:11.949040

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f2c3361d2bb'
down_revision = '899d03d2910a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('model_data_types', 'desc',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.Text(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('model_data_types', 'desc',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=500),
               existing_nullable=True)
    # ### end Alembic commands ###
