"""Rotas do recurso customers."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.database import DbSession
from app.models.customer import Customer
from app.schemas.common import Page, error_responses
from app.schemas.customer import CustomerCreate, CustomerRead

router = APIRouter(prefix="/api/customers", tags=["customers"])

DUPLICATE_EMAIL_DETAIL = "Já existe um cliente com este e-mail"


@router.get(
    "",
    summary="Lista os clientes cadastrados, paginado",
    response_model=Page[CustomerRead],
)
def list_customers(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100, description="Tamanho da página")] = 20,
    offset: Annotated[int, Query(ge=0, description="Deslocamento")] = 0,
) -> Page[CustomerRead]:
    """Devolve os clientes do mais recente para o mais antigo."""
    total = db.execute(select(func.count()).select_from(Customer)).scalar_one()
    customers = (
        db.execute(
            select(Customer)
            .order_by(Customer.created_at.desc(), Customer.id.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return Page[CustomerRead](
        items=[CustomerRead.model_validate(customer) for customer in customers],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    summary="Cadastra um cliente interessado",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409),
)
def create_customer(db: DbSession, payload: CustomerCreate) -> CustomerRead:
    """Cria o cliente; e-mail repetido responde 409."""
    customer = Customer(**payload.model_dump())
    db.add(customer)
    try:
        db.commit()
    except IntegrityError as exc:
        # A unicidade e garantida pelo banco, entao a corrida entre dois cadastros
        # simultaneos com o mesmo e-mail tambem cai aqui.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_EMAIL_DETAIL
        ) from exc

    db.refresh(customer)
    return CustomerRead.model_validate(customer)
