import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    counterparties: Mapped[list["Counterparty"]] = relationship(back_populates="owner")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="owner")


class CounterpartyType(str, enum.Enum):
    person = "person"
    company = "company"


class Counterparty(Base):
    __tablename__ = "counterparties"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_counterparty_owner_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[CounterpartyType] = mapped_column(
        Enum(CounterpartyType), default=CounterpartyType.company, nullable=False
    )
    inn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="counterparties")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="counterparty")


class ContractStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    closed = "closed"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    counterparty_id: Mapped[int] = mapped_column(
        ForeignKey("counterparties.id", ondelete="RESTRICT"), index=True
    )

    number: Mapped[str] = mapped_column(String(128), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus), default=ContractStatus.draft, nullable=False
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="contracts")
    counterparty: Mapped["Counterparty"] = relationship(back_populates="contracts")
    transactions: Mapped[list["ContractTransaction"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan"
    )


class TransactionType(str, enum.Enum):
    payment = "payment"
    act = "act"


class ContractTransaction(Base):
    __tablename__ = "contract_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(
        ForeignKey("contracts.id", ondelete="CASCADE"), index=True
    )

    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    contract: Mapped["Contract"] = relationship(back_populates="transactions")

