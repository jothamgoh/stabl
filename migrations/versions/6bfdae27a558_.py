"""empty message

Revision ID: 6bfdae27a558
Revises: 312ac1420015
Create Date: 2021-08-07 13:52:03.031880

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6bfdae27a558'
down_revision = '312ac1420015'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price_per_item_in_cents', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('discount_per_item_in_cents', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('quantity', sa.Integer(), nullable=False))
        batch_op.drop_column('price_paid_in_cents')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price_paid_in_cents', sa.INTEGER(), nullable=True))
        batch_op.drop_column('quantity')
        batch_op.drop_column('discount_per_item_in_cents')
        batch_op.drop_column('price_per_item_in_cents')

    # ### end Alembic commands ###
