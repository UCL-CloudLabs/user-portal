"""empty message

Revision ID: 8259c0ae0b4c
Revises: 0ebf5dad5713
Create Date: 2018-04-19 15:06:49.433443

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8259c0ae0b4c'
down_revision = '0ebf5dad5713'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('host', 'os_offer',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('host', 'os_sku',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('host', 'os_version',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('host', 'vm_type',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('host', 'vm_type',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('host', 'os_version',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('host', 'os_sku',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('host', 'os_offer',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    # ### end Alembic commands ###