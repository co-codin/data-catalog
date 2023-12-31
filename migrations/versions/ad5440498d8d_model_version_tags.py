"""model version tags

Revision ID: ad5440498d8d
Revises: f2f3046e3f4d
Create Date: 2023-05-19 19:51:06.583909

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad5440498d8d'
down_revision = 'f2f3046e3f4d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('model_version_tags',
    sa.Column('model_version_tags', sa.BigInteger(), nullable=False),
    sa.Column('tag_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['model_version_tags'], ['model_versions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
    sa.PrimaryKeyConstraint('model_version_tags', 'tag_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('model_version_tags')
    # ### end Alembic commands ###
