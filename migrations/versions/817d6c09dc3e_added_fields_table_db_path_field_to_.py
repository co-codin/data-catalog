"""added fields table + db_path field to objects table

Revision ID: 817d6c09dc3e
Revises: 89dc1f0baaf8
Create Date: 2023-06-02 15:36:58.883927

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '817d6c09dc3e'
down_revision = '89dc1f0baaf8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fields',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('object_guid', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('length', sa.Integer(), nullable=False),
    sa.Column('is_key', sa.Boolean(), nullable=False),
    sa.Column('db_path', sa.String(), nullable=False),
    sa.Column('owner', sa.String(length=144), nullable=False),
    sa.Column('desc', sa.Text(), nullable=True),
    sa.Column('source_created_at', sa.DateTime(), nullable=True),
    sa.Column('source_updated_at', sa.DateTime(), nullable=True),
    sa.Column('local_updated_at', sa.DateTime(), nullable=False),
    sa.Column('synchronized_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['object_guid'], ['objects.guid'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fields_guid'), 'fields', ['guid'], unique=True)
    op.create_table('fields_tags',
    sa.Column('field_id', sa.BigInteger(), nullable=False),
    sa.Column('tag_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['field_id'], ['fields.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
    sa.PrimaryKeyConstraint('field_id', 'tag_id')
    )
    op.add_column('comments', sa.Column('field_guid', sa.String(length=36), nullable=True))
    op.create_foreign_key(None, 'comments', 'fields', ['field_guid'], ['guid'], ondelete='CASCADE')
    op.add_column('objects', sa.Column('db_path', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('objects', 'db_path')
    op.drop_constraint(None, 'comments', type_='foreignkey')
    op.drop_column('comments', 'field_guid')
    op.drop_table('fields_tags')
    op.drop_index(op.f('ix_fields_guid'), table_name='fields')
    op.drop_table('fields')
    # ### end Alembic commands ###
