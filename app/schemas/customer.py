"""Schemas do recurso customers."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Cep = Annotated[str, Field(pattern=r"^\d{8}$", description="CEP com 8 digitos, sem mascara")]
State = Annotated[str, Field(pattern=r"^[A-Za-z]{2}$", description="UF com 2 letras")]


class CustomerCreate(BaseModel):
    """Dados do cliente interessado, com o endereco inline."""

    full_name: Annotated[str, Field(min_length=3, max_length=120, description="Nome completo")]
    email: Annotated[EmailStr, Field(description="E-mail, unico por cliente")]
    phone: Annotated[str | None, Field(default=None, max_length=20, description="Telefone")]
    cep: Cep
    street: Annotated[str, Field(min_length=1, max_length=200, description="Logradouro")]
    number: Annotated[str, Field(min_length=1, max_length=20, description="Numero")]
    complement: Annotated[
        str | None, Field(default=None, max_length=100, description="Complemento")
    ]
    district: Annotated[str | None, Field(default=None, max_length=100, description="Bairro")]
    city: Annotated[str, Field(min_length=1, max_length=100, description="Cidade")]
    state: State

    @field_validator("state")
    @classmethod
    def uppercase_state(cls, value: str) -> str:
        """Grava a UF sempre em maiusculas."""
        return value.upper()


class CustomerRead(BaseModel):
    """Um cliente cadastrado."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Identificador do cliente")
    full_name: str = Field(description="Nome completo")
    email: EmailStr = Field(description="E-mail")
    phone: str | None = Field(description="Telefone")
    cep: str = Field(description="CEP, so digitos")
    street: str = Field(description="Logradouro")
    number: str = Field(description="Numero")
    complement: str | None = Field(description="Complemento")
    district: str | None = Field(description="Bairro")
    city: str = Field(description="Cidade")
    state: str = Field(description="UF")
    created_at: datetime = Field(description="Momento do cadastro")
