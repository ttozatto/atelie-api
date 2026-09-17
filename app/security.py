"""Protecao das rotas de escrita do painel.

ATENCAO: isto NAO e autenticacao. E um placeholder de MVP academico que compara um
header com uma variavel de ambiente — nao ha usuarios, sessoes, hash de senha nem
expiracao de credencial. Num sistema real, trocar por autenticacao de verdade
(OAuth2/OIDC, sessao assinada ou JWT com rotacao de chave).
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import get_settings


def require_admin_token(
    x_admin_token: Annotated[
        str | None,
        Header(description="Token do painel, comparado com a variável ADMIN_TOKEN"),
    ] = None,
) -> None:
    """Recusa a requisicao se o header X-Admin-Token nao bater com ADMIN_TOKEN."""
    if x_admin_token != get_settings().admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token do painel inválido ou ausente",
        )


#: Dependency usada nas rotas de escrita de fotos.
AdminGuard = Annotated[None, Depends(require_admin_token)]
