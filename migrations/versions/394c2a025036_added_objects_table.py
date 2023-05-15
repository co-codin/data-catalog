"""added objects table

Revision ID: 394c2a025036
Revises: 70ec5d7c5916
Create Date: 2023-05-10 14:59:02.325559

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '394c2a025036'
down_revision = '70ec5d7c5916'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('objects',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('owner', sa.String(length=144), nullable=False),
    sa.Column('source_created_at', sa.DateTime(), nullable=True),
    sa.Column('source_updated_at', sa.DateTime(), nullable=True),
    sa.Column('local_updated_at', sa.DateTime(), nullable=False),
    sa.Column('synchronized_at', sa.DateTime(), nullable=True),
    sa.Column('short_desc', sa.Text(), nullable=True),
    sa.Column('business_desc', sa.Text(), nullable=True),
    sa.Column('is_synchronized', sa.Boolean(), nullable=False),
    sa.Column('source_registry_guid', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['source_registry_guid'], ['source_registers.guid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_objects_guid'), 'objects', ['guid'], unique=True)
    op.create_table('objects_tags',
    sa.Column('object_id', sa.BigInteger(), nullable=False),
    sa.Column('tag_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['object_id'], ['objects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
    sa.PrimaryKeyConstraint('object_id', 'tag_id')
    )
    op.add_column('comments', sa.Column('object_guid', sa.String(length=36), nullable=True))
    op.create_foreign_key(None, 'comments', 'objects', ['object_guid'], ['guid'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'comments', type_='foreignkey')
    op.drop_column('comments', 'object_guid')
    op.drop_table('objects_tags')
    op.drop_index(op.f('ix_objects_guid'), table_name='objects')
    op.drop_table('objects')
    # ### end Alembic commands ###
