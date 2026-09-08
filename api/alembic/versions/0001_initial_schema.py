"""initial schema: users, apartments, reservations, amenities, apartment_amenities

Revision ID: 0001
Revises:
Create Date: 2026-08-27

Creates the full initial schema:
  users        1 -> N apartments        (apartments.owner_id)
  users        1 -> N reservations       (reservations.guest_id)
  apartments   1 -> N reservations       (reservations.apartment_id)
  apartments   N -> M amenities          (apartment_amenities)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="USER"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "apartments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "owner_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("image", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("price_per_night", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_guests", sa.Integer, nullable=False),
        sa.Column("bedrooms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("bathrooms", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_apartments_owner_id", "apartments", ["owner_id"])
    op.create_index("ix_apartments_city", "apartments", ["city"])

    op.create_table(
        "amenities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.UniqueConstraint("name", name="uq_amenities_name"),
    )

    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "apartment_id",
            sa.Integer,
            sa.ForeignKey("apartments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "guest_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("check_in", sa.Date, nullable=False),
        sa.Column("check_out", sa.Date, nullable=False),
        sa.Column("guests_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_reservations_apartment_id", "reservations", ["apartment_id"])
    op.create_index("ix_reservations_guest_id", "reservations", ["guest_id"])

    op.create_table(
        "apartment_amenities",
        sa.Column(
            "apartment_id",
            sa.Integer,
            sa.ForeignKey("apartments.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "amenity_id",
            sa.Integer,
            sa.ForeignKey("amenities.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("apartment_amenities")
    op.drop_index("ix_reservations_guest_id", table_name="reservations")
    op.drop_index("ix_reservations_apartment_id", table_name="reservations")
    op.drop_table("reservations")
    op.drop_table("amenities")
    op.drop_index("ix_apartments_city", table_name="apartments")
    op.drop_index("ix_apartments_owner_id", table_name="apartments")
    op.drop_table("apartments")
    op.drop_table("users")
