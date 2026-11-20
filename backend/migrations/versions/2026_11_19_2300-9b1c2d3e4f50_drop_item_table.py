"""drop item table

Revision ID: 9b1c2d3e4f50
Revises: e97db85c3a70
Create Date: 2026-11-19 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b1c2d3e4f50'
down_revision: Union[str, None] = 'e97db85c3a70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_item_name'), table_name='item')
    op.drop_table('item')


def downgrade() -> None:
    op.create_table(
        'item',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_item_name'), 'item', ['name'], unique=False)
