"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-03-16

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("user", "admin", name="userrole"), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "counterparties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "type",
            sa.Enum("person", "company", name="counterpartytype"),
            nullable=False,
            server_default="company",
        ),
        sa.Column("inn", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_counterparties_owner_id", "counterparties", ["owner_id"])
    op.create_unique_constraint("uq_counterparty_owner_name", "counterparties", ["owner_id", "name"])

    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "counterparty_id",
            sa.Integer(),
            sa.ForeignKey("counterparties.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("number", sa.String(length=128), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "closed", name="contractstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_contracts_owner_id", "contracts", ["owner_id"])
    op.create_index("ix_contracts_counterparty_id", "contracts", ["counterparty_id"])

    op.create_table(
        "contract_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "type",
            sa.Enum("payment", "act", name="transactiontype"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_contract_transactions_contract_id", "contract_transactions", ["contract_id"])


def downgrade() -> None:
    op.drop_index("ix_contract_transactions_contract_id", table_name="contract_transactions")
    op.drop_table("contract_transactions")

    op.drop_index("ix_contracts_counterparty_id", table_name="contracts")
    op.drop_index("ix_contracts_owner_id", table_name="contracts")
    op.drop_table("contracts")

    op.drop_constraint("uq_counterparty_owner_name", "counterparties", type_="unique")
    op.drop_index("ix_counterparties_owner_id", table_name="counterparties")
    op.drop_table("counterparties")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS contractstatus")
    op.execute("DROP TYPE IF EXISTS counterpartytype")
    op.execute("DROP TYPE IF EXISTS userrole")

