"""Schemas reaproveitados por mais de um recurso."""

from pydantic import BaseModel, Field


class Page[ItemType](BaseModel):
    """Pagina de resultados com o total disponivel."""

    items: list[ItemType] = Field(description="Itens desta pagina")
    total: int = Field(description="Total de registros que atendem ao filtro")
    limit: int = Field(description="Tamanho da pagina usado na consulta")
    offset: int = Field(description="Deslocamento usado na consulta")


class MessageResponse(BaseModel):
    """Resposta simples de confirmacao."""

    detail: str = Field(description="Mensagem de confirmacao")
