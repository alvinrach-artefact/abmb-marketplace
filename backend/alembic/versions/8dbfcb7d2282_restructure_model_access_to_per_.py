"""restructure model access to per-capability grants

Revision ID: 8dbfcb7d2282
Revises: f0f13ff71128
Create Date: 2026-09-27 20:32:20.424379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '8dbfcb7d2282'
down_revision: Union[str, Sequence[str], None] = 'f0f13ff71128'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the new column nullable first -- can't be NOT NULL yet, table has rows.
    op.add_column('agent_model_access', sa.Column('requested_capability', sa.Text(), nullable=True))

    # 2. Backfill from the old column instead of losing the data.
    op.execute("UPDATE agent_model_access SET requested_capability = model_name")

    # 3. Now safe to enforce NOT NULL.
    op.alter_column('agent_model_access', 'requested_capability', nullable=False)

    # 4. New nullable column for the admin's later grant.
    op.add_column('agent_model_access', sa.Column('granted_model_name', sa.Text(), nullable=True))

    # 5. Drop the old columns.
    op.drop_column('agent_model_access', 'kind')
    op.drop_column('agent_model_access', 'model_name')

    # 6. Drop the now-orphaned enum type -- autogenerate never does this on its own.
    op.execute("DROP TYPE model_access_kind")


def downgrade() -> None:
    # Reverse order: recreate the type, then the columns, backfilling as we go.
    op.execute("CREATE TYPE model_access_kind AS ENUM ('requested', 'granted')")

    op.add_column('agent_model_access', sa.Column('model_name', sa.Text(), nullable=True))
    op.execute("UPDATE agent_model_access SET model_name = requested_capability")
    op.alter_column('agent_model_access', 'model_name', nullable=False)

    op.add_column(
        'agent_model_access',
        sa.Column('kind', postgresql.ENUM('requested', 'granted', name='model_access_kind', create_type=False),
                   nullable=True)
    )
    op.execute("UPDATE agent_model_access SET kind = 'granted' WHERE granted_model_name IS NOT NULL")
    op.execute("UPDATE agent_model_access SET kind = 'requested' WHERE kind IS NULL")
    op.alter_column('agent_model_access', 'kind', nullable=False)

    op.drop_column('agent_model_access', 'granted_model_name')
    op.drop_column('agent_model_access', 'requested_capability')