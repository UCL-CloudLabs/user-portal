"""empty message

Revision ID: c751facdbfdb
Revises: 
Create Date: 2017-07-18 14:47:37.179476

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c751facdbfdb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('upi', sa.String(length=7), nullable=False),
        sa.Column('ucl_id', sa.String(length=7), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_user_ucl_id'), 'user', ['ucl_id'], unique=True)
    op.create_index(op.f('ix_user_upi'), 'user', ['upi'], unique=True)
    op.create_table(
        'ssh_key',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=50), nullable=False),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'host',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dns_name', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('admin_username', sa.String(length=50), nullable=False),
        sa.Column('admin_password', sa.String(length=255), nullable=True),
        sa.Column('terraform_state', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('admin_ssh_key_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['admin_ssh_key_id'], ['ssh_key.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_host_dns_name'), 'host', ['dns_name'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_host_dns_name'), table_name='host')
    op.drop_table('host')
    op.drop_table('ssh_key')
    op.drop_index(op.f('ix_user_upi'), table_name='user')
    op.drop_index(op.f('ix_user_ucl_id'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
