"""empty message

Revision ID: 0529342cc859
Revises: 0e8b355adb04
Create Date: 2025-02-23 13:40:02.984441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0529342cc859'
down_revision: Union[str, None] = '0e8b355adb04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('scheduler',
    sa.Column('task_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('scheduled_time', sa.DateTime(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('retry_count', sa.Integer(), nullable=False),
    sa.Column('exception_info', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', mysql.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('status', postgresql.ENUM('1', '2', '3', '4', name='schedule_status'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduler_status'), 'scheduler', ['status'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_scheduler_status'), table_name='scheduler')
    op.drop_table('scheduler')
    # ### end Alembic commands ###
