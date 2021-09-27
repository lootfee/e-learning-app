"""empty message

Revision ID: a5f7a3bb3c14
Revises: ef56d19b2ba3
Create Date: 2021-08-11 15:37:45.773957

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5f7a3bb3c14'
down_revision = 'ef56d19b2ba3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('activity_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('log', sa.String(length=1000), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('bulletin', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'bulletin', 'activity_log', ['log_id'], ['id'])
    op.add_column('bulletin_attachment', sa.Column('deleted', sa.Boolean(), nullable=True))
    op.add_column('bulletin_attachment', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'bulletin_attachment', 'activity_log', ['log_id'], ['id'])
    op.add_column('bulletin_comment', sa.Column('deleted', sa.Boolean(), nullable=True))
    op.add_column('bulletin_comment', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'bulletin_comment', 'activity_log', ['log_id'], ['id'])
    op.add_column('bulletin_topic', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'bulletin_topic', 'activity_log', ['log_id'], ['id'])
    op.add_column('cme_content_slides', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'cme_content_slides', 'activity_log', ['log_id'], ['id'])
    op.add_column('cme_content_video', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'cme_content_video', 'activity_log', ['log_id'], ['id'])
    op.add_column('cme_course', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'cme_course', 'activity_log', ['log_id'], ['id'])
    op.add_column('cme_course_content', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'cme_course_content', 'activity_log', ['log_id'], ['id'])
    op.add_column('cme_course_question', sa.Column('log_id', sa.Integer(), nullable=True))
    op.add_column('cme_course_question', sa.Column('deleted', sa.Boolean(), nullable=True))
    op.create_foreign_key(None, 'cme_course_question', 'activity_log', ['log_id'], ['id'])
    op.add_column('cme_course_question_choices', sa.Column('deleted', sa.Boolean(), nullable=True))
    op.add_column('cme_course_question_choices', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'cme_course_question_choices', 'activity_log', ['log_id'], ['id'])
    op.add_column('cme_course_topic', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'cme_course_topic', 'activity_log', ['log_id'], ['id'])
    op.add_column('designation', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'designation', 'activity_log', ['log_id'], ['id'])
    op.add_column('push_subscription', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'push_subscription', 'activity_log', ['log_id'], ['id'])
    op.add_column('role', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'role', 'activity_log', ['log_id'], ['id'])
    op.add_column('user', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'activity_log', ['log_id'], ['id'])
    op.add_column('user_activation', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user_activation', 'activity_log', ['log_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user_activation', type_='foreignkey')
    op.drop_column('user_activation', 'log_id')
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'log_id')
    op.drop_constraint(None, 'role', type_='foreignkey')
    op.drop_column('role', 'log_id')
    op.drop_constraint(None, 'push_subscription', type_='foreignkey')
    op.drop_column('push_subscription', 'log_id')
    op.drop_constraint(None, 'designation', type_='foreignkey')
    op.drop_column('designation', 'log_id')
    op.drop_constraint(None, 'cme_course_topic', type_='foreignkey')
    op.drop_column('cme_course_topic', 'log_id')
    op.drop_constraint(None, 'cme_course_question_choices', type_='foreignkey')
    op.drop_column('cme_course_question_choices', 'log_id')
    op.drop_column('cme_course_question_choices', 'deleted')
    op.drop_constraint(None, 'cme_course_question', type_='foreignkey')
    op.drop_column('cme_course_question', 'deleted')
    op.drop_column('cme_course_question', 'log_id')
    op.drop_constraint(None, 'cme_course_content', type_='foreignkey')
    op.drop_column('cme_course_content', 'log_id')
    op.drop_constraint(None, 'cme_course', type_='foreignkey')
    op.drop_column('cme_course', 'log_id')
    op.drop_constraint(None, 'cme_content_video', type_='foreignkey')
    op.drop_column('cme_content_video', 'log_id')
    op.drop_constraint(None, 'cme_content_slides', type_='foreignkey')
    op.drop_column('cme_content_slides', 'log_id')
    op.drop_constraint(None, 'bulletin_topic', type_='foreignkey')
    op.drop_column('bulletin_topic', 'log_id')
    op.drop_constraint(None, 'bulletin_comment', type_='foreignkey')
    op.drop_column('bulletin_comment', 'log_id')
    op.drop_column('bulletin_comment', 'deleted')
    op.drop_constraint(None, 'bulletin_attachment', type_='foreignkey')
    op.drop_column('bulletin_attachment', 'log_id')
    op.drop_column('bulletin_attachment', 'deleted')
    op.drop_constraint(None, 'bulletin', type_='foreignkey')
    op.drop_column('bulletin', 'log_id')
    op.drop_table('activity_log')
    # ### end Alembic commands ###
