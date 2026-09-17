"""Schema do endereco devolvido pelo proxy de CEP.

Este e o nosso contrato: os nomes vem em ingles e no formato que a interface usa,
independentemente de como o ViaCEP nomeia os campos dele.
"""

from pydantic import BaseModel, Field


class AddressResponse(BaseModel):
    """Endereco resolvido a partir de um CEP."""

    cep: str = Field(description="CEP consultado, só dígitos", examples=["01001000"])
    street: str = Field(description="Logradouro (logradouro no ViaCEP)", examples=["Praça da Sé"])
    district: str = Field(description="Bairro (bairro no ViaCEP)", examples=["Sé"])
    city: str = Field(description="Cidade (localidade no ViaCEP)", examples=["São Paulo"])
    state: str = Field(description="UF (uf no ViaCEP)", examples=["SP"])
