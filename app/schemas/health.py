"""Schemas da rota de health check."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Situacao da API e da conexao com o banco."""

    status: Literal["ok"] = Field(description="Situação geral da API")
    database: Literal["ok"] = Field(description="Situação da conexão com o PostgreSQL")
