"""widen apartments.image to TEXT (allow uploaded base64 data URIs)

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "apartments",
        "image",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "apartments",
        "image",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
