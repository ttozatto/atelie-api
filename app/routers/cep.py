"""Rota do proxy de CEP."""

from typing import Annotated

from fastapi import APIRouter, Path

from app.schemas.address import AddressResponse
from app.services.viacep import fetch_address

router = APIRouter(prefix="/api/cep", tags=["cep"])


@router.get(
    "/{cep}",
    summary="Consulta um CEP no ViaCEP e devolve o endereco no nosso formato",
    response_model=AddressResponse,
    responses={
        404: {"description": "CEP nao encontrado"},
        502: {"description": "Servico de CEP indisponivel"},
        504: {"description": "Servico de CEP nao respondeu a tempo"},
    },
)
async def read_cep(
    cep: Annotated[
        str,
        Path(
            pattern=r"^\d{8}$",
            description="CEP com 8 digitos, sem mascara",
            examples=["01001000"],
        ),
    ],
) -> AddressResponse:
    """Devolve logradouro, bairro, cidade e UF do CEP informado."""
    return await fetch_address(cep)
