"""empty message

Revision ID: 6dd8ce1b7a42
Revises: 42ce72fc37b2
Create Date: 2021-08-11 10:53:30.117585

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6dd8ce1b7a42'
down_revision = '42ce72fc37b2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_activation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('date_activated', sa.DateTime(), nullable=True),
    sa.Column('date_inactivated', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('user', sa.Column('deleted', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'deleted')
    op.drop_table('user_activation')
    # ### end Alembic commands ###