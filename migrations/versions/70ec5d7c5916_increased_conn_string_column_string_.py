"""increased conn_string column string value to 728

Revision ID: 70ec5d7c5916
Revises: 85510f0ddbf1
Create Date: 2023-05-03 12:51:43.206495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70ec5d7c5916'
down_revision = '85510f0ddbf1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('source_registers', 'conn_string',
               existing_type=sa.VARCHAR(length=500),
               type_=sa.String(length=728),
               existing_nullable=False)
    op.drop_constraint('source_registers_conn_string_key', 'source_registers', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('source_registers_conn_string_key', 'source_registers', ['conn_string'])
    op.alter_column('source_registers', 'conn_string',
               existing_type=sa.String(length=728),
               type_=sa.VARCHAR(length=500),
               existing_nullable=False)
    # ### end Alembic commands ###
