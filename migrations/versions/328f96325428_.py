"""empty message

Revision ID: 328f96325428
Revises: 8ec76aaa7a22
Create Date: 2021-06-26 13:23:21.583035

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '328f96325428'
down_revision = '8ec76aaa7a22'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_designation')
    op.add_column('user', sa.Column('designation_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'designation', ['designation_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'designation_id')
    op.create_table('user_designation',
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('designation_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['designation_id'], ['designation.id'], name='user_designation_designation_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='user_designation_user_id_fkey')
    )
    # ### end Alembic commands ###
