"""model version comments

Revision ID: 4856ec8d43bd
Revises: 0270fcc14bbd
Create Date: 2023-05-25 10:50:18.718763

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4856ec8d43bd'
down_revision = '0270fcc14bbd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comments', sa.Column('model_version_guid', sa.String(length=36), nullable=True))
    op.create_foreign_key(None, 'comments', 'model_versions', ['model_version_guid'], ['guid'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'comments', type_='foreignkey')
    op.drop_column('comments', 'model_version_guid')
    # ### end Alembic commands ###
