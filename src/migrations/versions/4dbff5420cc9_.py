"""empty message

Revision ID: 4dbff5420cc9
Revises: 8c39c1a67655
Create Date: 2018-01-23 11:29:53.310240

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = '4dbff5420cc9'
down_revision = '8c39c1a67655'
branch_labels = None
depends_on = None


old_type = ENUM('defining',
                'deploying',
                'starting',
                'running',
                'stopped',
                'destroying',
                'error',
                name='hoststatus',
                create_type=False)
tmp_type = ENUM('defining',
                'deploying',
                'starting',
                'running',
                'stopped',
                'destroying',
                'error',
                name='tmp_hoststatus',
                create_type=False)
new_type = ENUM('defining',
                'deploying',
                'starting',
                'running',
                'stopped',
                'destroying',
                'error',
                'unknown',
                name='hoststatus',
                create_type=False)


def upgrade():
    # Create a temporary copy of the old type and convert the table to use it
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.alter_column('host', 'status', server_default=None)
    op.alter_column(
        'host', 'status',
        existing_type=old_type,
        type_=tmp_type,
        postgresql_using='status::text::tmp_hoststatus',
        existing_nullable=False,
        server_default=None)
    old_type.drop(op.get_bind(), checkfirst=False)
    # Now create the new type and convert the table to that
    new_type.create(op.get_bind(), checkfirst=False)
    op.alter_column(
        'host', 'status',
        existing_type=tmp_type,
        type_=new_type,
        postgresql_using="status::text::hoststatus",
        existing_nullable=False,
        server_default=sa.text("'defining'::hoststatus"))
    tmp_type.drop(op.get_bind(), checkfirst=False)


def downgrade():
    # Convert any values in the column using the status to be removed
    op.execute(
        "UPDATE host SET status='error'::hoststatus WHERE status='unknown'::hoststatus")
    # Create a temporary copy of the old type and convert the table to use it
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.alter_column('host', 'status', server_default=None)
    op.alter_column(
        'host', 'status',
        existing_type=new_type,
        type_=tmp_type,
        postgresql_using='status::text::tmp_hoststatus',
        existing_nullable=False,
        server_default=None)
    new_type.drop(op.get_bind(), checkfirst=False)
    # Now create the old type and convert the table to that
    old_type.create(op.get_bind(), checkfirst=False)
    op.alter_column(
        'host', 'status',
        existing_type=tmp_type,
        type_=old_type,
        postgresql_using="status::text::hoststatus",
        existing_nullable=False,
        server_default=sa.text("'defining'::hoststatus"))
    tmp_type.drop(op.get_bind(), checkfirst=False)
