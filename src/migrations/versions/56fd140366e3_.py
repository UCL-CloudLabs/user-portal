"""empty message

Revision ID: 56fd140366e3
Revises: c751facdbfdb
Create Date: 2017-07-21 13:09:16.075771

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56fd140366e3'
down_revision = 'c751facdbfdb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('host', sa.Column('git_repo', sa.String(length=1024), nullable=True))
    op.add_column('host', sa.Column('port', sa.Integer(), nullable=True))
    op.add_column('host', sa.Column('setup_script', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('host', 'setup_script')
    op.drop_column('host', 'port')
    op.drop_column('host', 'git_repo')
    # ### end Alembic commands ###
