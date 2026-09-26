"""Rota de login do painel.

ATENCAO: continua sendo um placeholder de MVP academico, nao autenticacao de verdade.
Existe um unico usuario, vindo de variavel de ambiente; a senha e comparada em texto
puro (sem hash) e o token devolvido e um segredo compartilhado fixo, sem expiracao e sem
assinatura. Num sistema real, trocar por usuarios persistidos com senha em hash e sessao
ou token assinado com expiracao.
"""

import secrets

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import error_responses

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    summary="Autentica o painel com usuário e senha",
    response_model=LoginResponse,
    responses=error_responses(401),
)
def login(payload: LoginRequest) -> LoginResponse:
    """Confere as credenciais e devolve o token usado nas rotas de escrita."""
    settings = get_settings()
    # compare_digest nos dois campos, sem curto-circuito: o tempo de resposta nao revela
    # se o que estava errado era o usuario ou a senha.
    username_ok = secrets.compare_digest(payload.username, settings.admin_username)
    password_ok = secrets.compare_digest(payload.password, settings.admin_password)
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    return LoginResponse(username=settings.admin_username, token=settings.admin_token)
