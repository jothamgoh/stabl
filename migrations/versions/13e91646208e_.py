"""empty message

Revision ID: 13e91646208e
Revises: 6bfdae27a558
Create Date: 2021-08-09 18:34:24.154086

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13e91646208e'
down_revision = '6bfdae27a558'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order_number', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer_orders', schema=None) as batch_op:
        batch_op.drop_column('order_number')

    # ### end Alembic commands ###