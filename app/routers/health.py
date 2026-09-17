"""Rota de health check."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import DbSession
from app.schemas.common import error_responses
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Verifica a API e a conexão com o banco",
    response_model=HealthResponse,
    responses=error_responses(503),
)
def read_health(db: DbSession) -> HealthResponse:
    """Executa um SELECT 1 para confirmar que o PostgreSQL responde."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Banco de dados indisponível",
        ) from exc
    return HealthResponse(status="ok", database="ok")
