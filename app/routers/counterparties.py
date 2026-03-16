from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import CounterpartyCreate, CounterpartyOut, CounterpartyUpdate
from app.services import CounterpartyService


router = APIRouter(prefix="/counterparties", tags=["counterparties"])


@router.get("", response_model=list[CounterpartyOut])
def list_counterparties(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return CounterpartyService(db, user).list()


@router.post("", response_model=CounterpartyOut)
def create_counterparty(
    payload: CounterpartyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return CounterpartyService(db, user).create(name=payload.name, type=payload.type, inn=payload.inn)


@router.get("/{counterparty_id}", response_model=CounterpartyOut)
def get_counterparty(
    counterparty_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return CounterpartyService(db, user).get(counterparty_id)


@router.patch("/{counterparty_id}", response_model=CounterpartyOut)
def update_counterparty(
    counterparty_id: int,
    payload: CounterpartyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return CounterpartyService(db, user).update(
        counterparty_id, name=payload.name, type=payload.type, inn=payload.inn
    )


@router.delete("/{counterparty_id}", status_code=204)
def delete_counterparty(
    counterparty_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    CounterpartyService(db, user).delete(counterparty_id)

