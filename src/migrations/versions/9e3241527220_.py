"""empty message

Revision ID: 9e3241527220
Revises: 1fb97ad680d5
Create Date: 2018-04-19 17:17:37.152023

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e3241527220'
down_revision = '1fb97ad680d5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('host', sa.Column('os_publisher', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('host', 'os_publisher')
    # ### end Alembic commands ###