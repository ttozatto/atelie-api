"""Schemas reaproveitados por mais de um recurso."""

from pydantic import BaseModel, Field


class Page[ItemType](BaseModel):
    """Pagina de resultados com o total disponivel."""

    items: list[ItemType] = Field(description="Itens desta página")
    total: int = Field(description="Total de registros que atendem ao filtro")
    limit: int = Field(description="Tamanho da página usado na consulta")
    offset: int = Field(description="Deslocamento usado na consulta")


class ErrorResponse(BaseModel):
    """Formato de todos os erros da API."""

    detail: str = Field(description="Descrição do erro")


def error_responses(*codes: int) -> dict[int | str, dict[str, object]]:
    """Documenta no Swagger os codigos de erro de uma rota com o schema ErrorResponse."""
    descriptions = {
        401: "Token do painel inválido ou ausente",
        404: "Recurso não encontrado",
        409: "Conflito com um registro existente",
        413: "Arquivo acima do limite",
        415: "Formato de arquivo não suportado",
        502: "Serviço externo indisponível",
        503: "Dependência indisponível",
        504: "Serviço externo não respondeu a tempo",
    }
    return {code: {"model": ErrorResponse, "description": descriptions[code]} for code in codes}


class MessageResponse(BaseModel):
    """Resposta simples de confirmacao."""

    detail: str = Field(description="Mensagem de confirmação")
