"""operation relation

Revision ID: 7e10e8ac9384
Revises: ed2190a00573
Create Date: 2023-07-06 09:48:16.691671

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7e10e8ac9384'
down_revision = 'ed2190a00573'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('model_relation_operations',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('model_relation_id', sa.BigInteger(), nullable=True),
    sa.Column('operation_body_id', sa.BigInteger(), nullable=True),
    sa.Column('parent_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['model_relation_id'], ['model_relations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['operation_body_id'], ['operation_bodies.operation_body_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_relation_operations_guid'), 'model_relation_operations', ['guid'], unique=True)
    op.create_table('model_relation_operation_parameters',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('model_relation_operation_id', sa.BigInteger(), nullable=True),
    sa.Column('model_resource_attribute_id', sa.BigInteger(), nullable=True),
    sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['model_relation_operation_id'], ['model_relation_operations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['model_resource_attribute_id'], ['model_resource_attributes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_relation_operation_parameters_guid'), 'model_relation_operation_parameters', ['guid'], unique=True)
    op.drop_constraint('model_relations_operation_id_fkey', 'model_relations', type_='foreignkey')
    op.drop_column('model_relations', 'operation_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('model_relations', sa.Column('operation_id', sa.BIGINT(), autoincrement=False, nullable=True))
    op.create_foreign_key('model_relations_operation_id_fkey', 'model_relations', 'operations', ['operation_id'], ['operation_id'])
    op.drop_index(op.f('ix_model_relation_operation_parameters_guid'), table_name='model_relation_operation_parameters')
    op.drop_table('model_relation_operation_parameters')
    op.drop_index(op.f('ix_model_relation_operations_guid'), table_name='model_relation_operations')
    op.drop_table('model_relation_operations')
    # ### end Alembic commands ###
