"""added comments into model

Revision ID: 7ee3c385109f
Revises: 08bcf434e18e
Create Date: 2023-05-23 10:10:17.015673

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ee3c385109f'
down_revision = '08bcf434e18e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comments', sa.Column('model_guid', sa.String(length=36), nullable=True))
    op.create_foreign_key(None, 'comments', 'models', ['model_guid'], ['guid'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'comments', type_='foreignkey')
    op.drop_column('comments', 'model_guid')
    # ### end Alembic commands ###
