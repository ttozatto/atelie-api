"""Rota do proxy de CEP."""

from typing import Annotated

from fastapi import APIRouter, Path

from app.schemas.address import AddressResponse
from app.schemas.common import error_responses
from app.services.viacep import fetch_address

router = APIRouter(prefix="/api/cep", tags=["cep"])


@router.get(
    "/{cep}",
    summary="Consulta um CEP no ViaCEP e devolve o endereço no nosso formato",
    response_model=AddressResponse,
    responses=error_responses(404, 502, 504),
)
async def read_cep(
    cep: Annotated[
        str,
        Path(
            pattern=r"^\d{8}$",
            description="CEP com 8 dígitos, sem máscara",
            examples=["01001000"],
        ),
    ],
) -> AddressResponse:
    """Devolve logradouro, bairro, cidade e UF do CEP informado."""
    return await fetch_address(cep)
