"""Schemas do recurso photos."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PhotoCategory(str, Enum):
    """Categorias aceitas para uma obra."""

    RETRATO = "retrato"
    PAISAGEM = "paisagem"
    URBANO = "urbano"
    AUTORAL = "autoral"


class PhotoMedium(str, Enum):
    """Suportes em que a obra e vendida."""

    PRINT = "print"
    QUADRO = "quadro"


class PhotoRead(BaseModel):
    """Uma obra do catalogo."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Identificador da obra")
    title: str = Field(description="Titulo da obra")
    description: str | None = Field(description="Texto livre sobre a obra")
    category: PhotoCategory | None = Field(description="Categoria da obra")
    medium: PhotoMedium = Field(description="Suporte: print ou quadro")
    sizes: list[str] = Field(description="Formatos disponiveis, ex.: ['A4', 'A3', '30x40']")
    price_cents: int = Field(description="Preco em centavos de real")
    image_path: str = Field(description="Caminho da imagem servida pela API, ex.: /media/a1b2.jpg")
    is_published: bool = Field(description="Se aparece na galeria publica")
    created_at: datetime = Field(description="Momento do cadastro")
