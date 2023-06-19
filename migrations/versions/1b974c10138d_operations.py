"""operations

Revision ID: 1b974c10138d
Revises: 3745083d4de3
Create Date: 2023-06-19 08:06:51.565205

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b974c10138d'
down_revision = '3745083d4de3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('operation_bodies',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('code', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_operation_bodies_guid'), 'operation_bodies', ['guid'], unique=True)
    op.create_table('operation_body_parameters',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('operation_body_id', sa.BigInteger(), nullable=True),
    sa.Column('flag', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('name_for_relation', sa.String(length=200), nullable=False),
    sa.Column('model_data_type_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['model_data_type_id'], ['model_data_types.id'], ),
    sa.ForeignKeyConstraint(['operation_body_id'], ['operation_bodies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_operation_body_parameters_guid'), 'operation_body_parameters', ['guid'], unique=True)
    op.create_table('operations',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('owner', sa.String(length=144), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('desc', sa.String(length=1000), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('operation_body_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['operation_body_id'], ['operation_bodies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_operations_guid'), 'operations', ['guid'], unique=True)
    op.create_table('operation_tags',
    sa.Column('operation_tags', sa.BigInteger(), nullable=False),
    sa.Column('tag_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['operation_tags'], ['operations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
    sa.PrimaryKeyConstraint('operation_tags', 'tag_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('operation_tags')
    op.drop_index(op.f('ix_operations_guid'), table_name='operations')
    op.drop_table('operations')
    op.drop_index(op.f('ix_operation_body_parameters_guid'), table_name='operation_body_parameters')
    op.drop_table('operation_body_parameters')
    op.drop_index(op.f('ix_operation_bodies_guid'), table_name='operation_bodies')
    op.drop_table('operation_bodies')
    # ### end Alembic commands ###
