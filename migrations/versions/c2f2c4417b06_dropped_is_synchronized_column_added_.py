"""dropped is_synchronized column, added default value ON to status column

Revision ID: c2f2c4417b06
Revises: 5ad8809614ca
Create Date: 2023-04-28 09:45:05.739765

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2f2c4417b06'
down_revision = '5ad8809614ca'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('source_registers', 'is_synchronized')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('source_registers', sa.Column('is_synchronized', sa.BOOLEAN(), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
