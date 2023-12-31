"""query_constructor

Revision ID: 5519327da8bb
Revises: 1b99ac0a9107
Create Date: 2023-06-22 07:13:49.565655

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5519327da8bb'
down_revision = '1b99ac0a9107'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('query_constructors',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('owner', sa.String(length=144), nullable=False),
    sa.Column('desc', sa.String(length=1000), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_constructors_guid'), 'query_constructors', ['guid'], unique=True)
    op.create_table('query_constructor_history',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('query_constructor_id', sa.BigInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('ended_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['query_constructor_id'], ['query_constructors.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_constructor_history_guid'), 'query_constructor_history', ['guid'], unique=True)
    op.create_table('query_constructor_reviewers',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('query_constructor_id', sa.BigInteger(), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['query_constructor_id'], ['query_constructors.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_constructor_reviewers_guid'), 'query_constructor_reviewers', ['guid'], unique=True)
    op.create_table('query_constructor_tags',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('tag_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['query_constructors.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
    sa.PrimaryKeyConstraint('id', 'tag_id')
    )
    op.create_table('query_constructor_bodies',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('query_constructor_id', sa.BigInteger(), nullable=True),
    sa.Column('model_version_id', sa.BigInteger(), nullable=True),
    sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('aggregators', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['query_constructor_id'], ['query_constructors.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_constructor_bodies_guid'), 'query_constructor_bodies', ['guid'], unique=True)
    op.create_table('query_constructor_body_fields',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('guid', sa.String(length=36), nullable=False),
    sa.Column('model_resource_attribute_id', sa.BigInteger(), nullable=True),
    sa.Column('query_constructor_body_id', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['model_resource_attribute_id'], ['model_resource_attributes.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['query_constructor_body_id'], ['query_constructor_bodies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_constructor_body_fields_guid'), 'query_constructor_body_fields', ['guid'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_query_constructor_body_fields_guid'), table_name='query_constructor_body_fields')
    op.drop_table('query_constructor_body_fields')
    op.drop_index(op.f('ix_query_constructor_bodies_guid'), table_name='query_constructor_bodies')
    op.drop_table('query_constructor_bodies')
    op.drop_table('query_constructor_tags')
    op.drop_index(op.f('ix_query_constructor_reviewers_guid'), table_name='query_constructor_reviewers')
    op.drop_table('query_constructor_reviewers')
    op.drop_index(op.f('ix_query_constructor_history_guid'), table_name='query_constructor_history')
    op.drop_table('query_constructor_history')
    op.drop_index(op.f('ix_query_constructors_guid'), table_name='query_constructors')
    op.drop_table('query_constructors')
    # ### end Alembic commands ###
