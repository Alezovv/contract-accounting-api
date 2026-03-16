import enum
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class CounterpartyType(str, enum.Enum):
    person = "person"
    company = "company"


class ContractStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    closed = "closed"


class TransactionType(str, enum.Enum):
    payment = "payment"
    act = "act"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime


class CounterpartyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: CounterpartyType = CounterpartyType.company
    inn: Optional[str] = Field(default=None, max_length=32)


class CounterpartyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    type: Optional[CounterpartyType] = None
    inn: Optional[str] = Field(default=None, max_length=32)


class CounterpartyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: CounterpartyType
    inn: Optional[str]
    created_at: datetime


class ContractCreate(BaseModel):
    counterparty_id: int
    number: str = Field(min_length=1, max_length=128)
    date: date
    total_amount: float = Field(gt=0)
    status: ContractStatus = ContractStatus.draft
    due_date: Optional[date] = None


class ContractUpdate(BaseModel):
    counterparty_id: Optional[int] = None
    number: Optional[str] = Field(default=None, min_length=1, max_length=128)
    date: Optional[date] = None
    total_amount: Optional[float] = Field(default=None, gt=0)
    status: Optional[ContractStatus] = None
    due_date: Optional[date] = None


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    counterparty_id: int
    number: str
    date: date
    total_amount: float
    status: ContractStatus
    due_date: Optional[date]
    created_at: datetime


class TransactionCreate(BaseModel):
    type: TransactionType
    amount: float = Field(gt=0)
    date: date


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    contract_id: int
    type: TransactionType
    amount: float
    date: date
    created_at: datetime


class ContractSettlementState(BaseModel):
    contract_id: int
    total_amount: float
    paid_amount: float
    remaining_amount: float
    is_fulfilled: bool

