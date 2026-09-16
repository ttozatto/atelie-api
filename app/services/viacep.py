"""Consumo do ViaCEP, o servico externo do sistema.

O ViaCEP e chamado aqui, nunca pelo navegador: a interface so conhece a nossa rota
`GET /api/cep/{cep}`. Este modulo traduz a resposta para o nosso schema e converte as
falhas do servico externo em erros HTTP nossos:

- `{"erro": true}`      -> 404 (CEP inexistente)
- timeout               -> 504 (o servico demorou demais)
- qualquer outra falha  -> 502 (o servico respondeu errado ou esta fora do ar)
"""

from typing import Any

import httpx
from fastapi import HTTPException, status

from app.config import get_settings
from app.schemas.address import AddressResponse


async def _request_viacep(cep: str) -> httpx.Response:
    """Faz a chamada HTTP ao ViaCEP para um CEP de 8 digitos."""
    settings = get_settings()
    url = f"{settings.viacep_base_url}/{cep}/json/"
    async with httpx.AsyncClient(timeout=settings.viacep_timeout_seconds) as client:
        return await client.get(url)


def _to_address(cep: str, payload: dict[str, Any]) -> AddressResponse:
    """Converte o corpo do ViaCEP no nosso schema de endereco."""
    return AddressResponse(
        cep=cep,
        street=payload.get("logradouro") or "",
        district=payload.get("bairro") or "",
        city=payload.get("localidade") or "",
        state=payload.get("uf") or "",
    )


async def fetch_address(cep: str) -> AddressResponse:
    """Busca o endereco de um CEP no ViaCEP, ja tratado e traduzido."""
    try:
        response = await _request_viacep(cep)
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Servico de CEP nao respondeu a tempo",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servico de CEP indisponivel",
        ) from exc

    if response.status_code != httpx.codes.OK:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servico de CEP indisponivel",
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servico de CEP devolveu uma resposta invalida",
        ) from exc

    # O ViaCEP sinaliza CEP inexistente com {"erro": true} e status 200.
    if not isinstance(payload, dict) or payload.get("erro"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CEP nao encontrado")

    return _to_address(cep, payload)
