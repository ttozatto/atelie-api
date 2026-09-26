"""Schemas da autenticacao do painel."""

from typing import Annotated

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credenciais informadas na tela de login do painel."""

    username: Annotated[str, Field(min_length=1, max_length=60, description="Usuário do painel")]
    password: Annotated[str, Field(min_length=1, max_length=200, description="Senha do painel")]


class LoginResponse(BaseModel):
    """Resultado de um login bem-sucedido."""

    username: str = Field(description="Usuário autenticado")
    token: str = Field(description="Token para enviar no header X-Admin-Token das rotas de escrita")
