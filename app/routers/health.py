"""Rota de health check."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import DbSession
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Verifica a API e a conexao com o banco",
    response_model=HealthResponse,
)
def read_health(db: DbSession) -> HealthResponse:
    """Executa um SELECT 1 para confirmar que o PostgreSQL responde."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Banco de dados indisponivel",
        ) from exc
    return HealthResponse(status="ok", database="ok")
