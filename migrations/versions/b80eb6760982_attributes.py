"""attributes

Revision ID: b80eb6760982
Revises: ba5c91b7ab06
Create Date: 2023-06-26 07:49:03.820899

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b80eb6760982'
down_revision = 'ba5c91b7ab06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('model_attitudes', sa.Column('left_attribute_id', sa.BigInteger(), nullable=True))
    op.add_column('model_attitudes', sa.Column('right_attribute_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key(None, 'model_attitudes', 'model_resource_attributes', ['left_attribute_id'], ['id'])
    op.create_foreign_key(None, 'model_attitudes', 'model_resource_attributes', ['right_attribute_id'], ['id'])
    op.alter_column('model_resource_attributes', 'cardinality',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('model_resource_attributes', 'cardinality',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.drop_constraint(None, 'model_attitudes', type_='foreignkey')
    op.drop_constraint(None, 'model_attitudes', type_='foreignkey')
    op.drop_column('model_attitudes', 'right_attribute_id')
    op.drop_column('model_attitudes', 'left_attribute_id')
    # ### end Alembic commands ###
