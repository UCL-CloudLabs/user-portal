"""empty message

Revision ID: 76f861afbc3e
Revises: b7b9b0baa205
Create Date: 2017-08-24 12:41:01.410886

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision = '76f861afbc3e'
down_revision = 'b7b9b0baa205'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    enum = ENUM('defining',
                'deploying',
                'starting',
                'running',
                'stopped',
                'error',
                name='hoststatus',
                create_type=False)
    enum.create(op.get_bind(), checkfirst=False)
    op.add_column('host',
                  sa.Column('status', enum, nullable=False, server_default='defining'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('host', 'status')
    ENUM(name='hoststatus').drop(op.get_bind(), checkfirst=False)
    # ### end Alembic commands ###