"""empty message

Revision ID: 8ec76aaa7a22
Revises: f9868519c839
Create Date: 2021-06-24 09:25:51.037346

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ec76aaa7a22'
down_revision = 'f9868519c839'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('designation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_constraint('user_designation_id_fkey', 'user', type_='foreignkey')
    op.drop_column('user', 'designation_id')
    op.add_column('user_designation', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('user_designation', sa.Column('designation_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user_designation', 'designation', ['designation_id'], ['id'])
    op.create_foreign_key(None, 'user_designation', 'user', ['user_id'], ['id'])
    op.drop_column('user_designation', 'name')
    op.drop_column('user_designation', 'id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_designation', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.add_column('user_designation', sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'user_designation', type_='foreignkey')
    op.drop_constraint(None, 'user_designation', type_='foreignkey')
    op.drop_column('user_designation', 'designation_id')
    op.drop_column('user_designation', 'user_id')
    op.add_column('user', sa.Column('designation_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('user_designation_id_fkey', 'user', 'user_designation', ['designation_id'], ['id'])
    op.drop_table('designation')
    # ### end Alembic commands ###
