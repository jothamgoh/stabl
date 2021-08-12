"""empty message

Revision ID: 00773c3f3da1
Revises: 13e91646208e
Create Date: 2021-08-12 21:58:30.509161

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00773c3f3da1'
down_revision = '13e91646208e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('item_name', sa.String(length=128), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customer_orders', schema=None) as batch_op:
        batch_op.drop_column('item_name')

    # ### end Alembic commands ###