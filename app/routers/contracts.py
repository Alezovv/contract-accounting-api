from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import (
    ContractCreate,
    ContractOut,
    ContractSettlementState,
    ContractUpdate,
    TransactionCreate,
    TransactionOut,
)
from app.services import ContractService


router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("", response_model=list[ContractOut])
def list_contracts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ContractService(db, user).list()


@router.post("", response_model=ContractOut)
def create_contract(
    payload: ContractCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return ContractService(db, user).create(**payload.model_dump())


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ContractService(db, user).get(contract_id)


@router.patch("/{contract_id}", response_model=ContractOut)
def update_contract(
    contract_id: int,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ContractService(db, user).update(contract_id, **payload.model_dump(exclude_unset=True))


@router.delete("/{contract_id}", status_code=204)
def delete_contract(contract_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ContractService(db, user).delete(contract_id)


@router.post("/{contract_id}/transactions", response_model=TransactionOut)
def add_transaction(
    contract_id: int,
    payload: TransactionCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = ContractService(db, user)
    tx = svc.add_transaction(contract_id, type=payload.type, amount=payload.amount, date=payload.date)

    # "Вау": простое уведомление в консоль при просрочке и неоплате.
    background.add_task(_notify_if_overdue, contract_id, user.id)
    return tx


@router.get("/{contract_id}/state", response_model=ContractSettlementState)
def contract_state(
    contract_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return ContractService(db, user).settlement_state(contract_id)


@router.get("/analytics/active-sum")
def analytics_active_sum(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"active_contracts_sum": ContractService(db, user).analytics_active_contracts_sum()}


@router.get("/analytics/payments-sum")
def analytics_payments_sum(
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {
        "payments_sum": ContractService(db, user).analytics_payments_sum(
            from_date=from_date, to_date=to_date
        )
    }


def _notify_if_overdue(contract_id: int, user_id: int) -> None:
    # Логика intentionally минимальная для MVP: читаем состояние и печатаем.
    from sqlalchemy import select

    from app.db import SessionLocal
    from app.models import Contract, TransactionType, ContractTransaction
    from sqlalchemy import func

    db = SessionLocal()
    try:
        c = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.owner_id == user_id))
        if not c or not c.due_date:
            return
        if c.due_date >= date.today():
            return
        paid = (
            db.scalar(
                select(func.coalesce(func.sum(ContractTransaction.amount), 0)).where(
                    ContractTransaction.contract_id == c.id,
                    ContractTransaction.type == TransactionType.payment,
                )
            )
            or 0
        )
        if float(paid) + 1e-5 < float(c.total_amount):
            print(
                f"[OVERDUE] contract_id={c.id} due_date={c.due_date} total={c.total_amount} paid={paid}"
            )
    finally:
        db.close()

