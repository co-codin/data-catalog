"""initial

Revision ID: af8c000c166c
Revises: 
Create Date: 2023-04-21 09:47:21.258623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af8c000c166c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('source_registers',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('type', sa.String(length=36), nullable=False),
    sa.Column('origin', sa.Enum('INTERNAL', 'PRIMARY', name='origin'), nullable=False),
    sa.Column('status', sa.Enum('ON', 'OFF', 'SYNCHRONIZING', name='status'), nullable=False),
    sa.Column('conn_string', sa.String(length=500), nullable=False),
    sa.Column('working_mode', sa.Enum('PASSIVE', 'ACTIVE', 'BATCHED', 'STREAMED', name='workingmode'), nullable=False),
    sa.Column('owner', sa.String(length=36), nullable=False),
    sa.Column('desc', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('synchronized_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('conn_string')
    )
    op.create_index(op.f('ix_source_registers_desc'), 'source_registers', ['desc'], unique=False)
    op.create_index(op.f('ix_source_registers_guid'), 'source_registers', ['guid'], unique=True)
    op.create_index(op.f('ix_source_registers_name'), 'source_registers', ['name'], unique=True)
    op.create_table('comments',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('author_guid', sa.String(length=36), nullable=False),
    sa.Column('msg', sa.String(length=10000), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('source_guid', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['source_guid'], ['source_registers.guid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_msg'), 'comments', ['msg'], unique=False)
    op.create_table('tags',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('source_guid', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['source_guid'], ['source_registers.guid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_table('tags')
    op.drop_index(op.f('ix_comments_msg'), table_name='comments')
    op.drop_table('comments')
    op.drop_index(op.f('ix_source_registers_name'), table_name='source_registers')
    op.drop_index(op.f('ix_source_registers_guid'), table_name='source_registers')
    op.drop_index(op.f('ix_source_registers_desc'), table_name='source_registers')
    op.drop_table('source_registers')
    # ### end Alembic commands ###
