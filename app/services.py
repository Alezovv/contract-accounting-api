from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Contract,
    ContractStatus,
    ContractTransaction,
    Counterparty,
    TransactionType,
    User,
)


class CounterpartyService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    def list(self) -> list[Counterparty]:
        return list(
            self.db.scalars(select(Counterparty).where(Counterparty.owner_id == self.user.id))
        )

    def get(self, counterparty_id: int) -> Counterparty:
        cp = self.db.scalar(
            select(Counterparty).where(
                Counterparty.id == counterparty_id, Counterparty.owner_id == self.user.id
            )
        )
        if not cp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counterparty not found")
        return cp

    def create(self, *, name: str, type: str, inn: str | None) -> Counterparty:
        cp = Counterparty(owner_id=self.user.id, name=name, type=type, inn=inn)
        self.db.add(cp)
        self.db.commit()
        self.db.refresh(cp)
        return cp

    def update(self, counterparty_id: int, **patch) -> Counterparty:
        cp = self.get(counterparty_id)
        for k, v in patch.items():
            if v is not None:
                setattr(cp, k, v)
        self.db.commit()
        self.db.refresh(cp)
        return cp

    def delete(self, counterparty_id: int) -> None:
        cp = self.get(counterparty_id)
        self.db.delete(cp)
        self.db.commit()


class ContractService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    def list(self) -> list[Contract]:
        return list(self.db.scalars(select(Contract).where(Contract.owner_id == self.user.id)))

    def get(self, contract_id: int) -> Contract:
        c = self.db.scalar(
            select(Contract).where(Contract.id == contract_id, Contract.owner_id == self.user.id)
        )
        if not c:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        return c

    def create(
        self,
        *,
        counterparty_id: int,
        number: str,
        date: date,
        total_amount: float,
        status: ContractStatus,
        due_date: date | None,
    ) -> Contract:
        _ = self._get_counterparty(counterparty_id)
        c = Contract(
            owner_id=self.user.id,
            counterparty_id=counterparty_id,
            number=number,
            date=date,
            total_amount=total_amount,
            status=status,
            due_date=due_date,
        )
        self.db.add(c)
        self.db.commit()
        self.db.refresh(c)
        return c

    def update(self, contract_id: int, **patch) -> Contract:
        c = self.get(contract_id)
        if patch.get("counterparty_id") is not None:
            self._get_counterparty(patch["counterparty_id"])
        for k, v in patch.items():
            if v is not None:
                setattr(c, k, v)
        self.db.commit()
        self.db.refresh(c)
        return c

    def delete(self, contract_id: int) -> None:
        c = self.get(contract_id)
        self.db.delete(c)
        self.db.commit()

    def add_transaction(self, contract_id: int, *, type: TransactionType, amount: float, date: date):
        c = self.get(contract_id)
        tx = ContractTransaction(contract_id=c.id, type=type, amount=amount, date=date)
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        return tx

    def settlement_state(self, contract_id: int) -> dict:
        c = self.get(contract_id)
        paid = (
            self.db.scalar(
                select(func.coalesce(func.sum(ContractTransaction.amount), 0)).where(
                    ContractTransaction.contract_id == c.id,
                    ContractTransaction.type == TransactionType.payment,
                )
            )
            or 0
        )
        total = float(c.total_amount)
        paid_f = float(paid)
        remaining = max(0.0, total - paid_f)
        return {
            "contract_id": c.id,
            "total_amount": total,
            "paid_amount": paid_f,
            "remaining_amount": remaining,
            "is_fulfilled": remaining <= 0.00001,
        }

    def analytics_active_contracts_sum(self) -> float:
        res = self.db.scalar(
            select(func.coalesce(func.sum(Contract.total_amount), 0)).where(
                Contract.owner_id == self.user.id,
                Contract.status == ContractStatus.active,
            )
        )
        return float(res or 0)

    def analytics_payments_sum(self, *, from_date: date, to_date: date) -> float:
        res = self.db.scalar(
            select(func.coalesce(func.sum(ContractTransaction.amount), 0))
            .join(Contract, Contract.id == ContractTransaction.contract_id)
            .where(
                Contract.owner_id == self.user.id,
                ContractTransaction.type == TransactionType.payment,
                ContractTransaction.date >= from_date,
                ContractTransaction.date <= to_date,
            )
        )
        return float(res or 0)

    def _get_counterparty(self, counterparty_id: int) -> Counterparty:
        cp = self.db.scalar(
            select(Counterparty).where(
                Counterparty.id == counterparty_id, Counterparty.owner_id == self.user.id
            )
        )
        if not cp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid counterparty")
        return cp

