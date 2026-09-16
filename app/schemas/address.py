"""Schema do endereco devolvido pelo proxy de CEP.

Este e o nosso contrato: os nomes vem em ingles e no formato que a interface usa,
independentemente de como o ViaCEP nomeia os campos dele.
"""

from pydantic import BaseModel, Field


class AddressResponse(BaseModel):
    """Endereco resolvido a partir de um CEP."""

    cep: str = Field(description="CEP consultado, so digitos", examples=["01001000"])
    street: str = Field(description="Logradouro (logradouro no ViaCEP)", examples=["Praca da Se"])
    district: str = Field(description="Bairro (bairro no ViaCEP)", examples=["Se"])
    city: str = Field(description="Cidade (localidade no ViaCEP)", examples=["Sao Paulo"])
    state: str = Field(description="UF (uf no ViaCEP)", examples=["SP"])
