"""Testes do proxy de CEP.

O ViaCEP e sempre mockado: nenhum teste sai para a rede.
"""

import httpx
import pytest

VIACEP_SUCESSO = {
    "cep": "01001-000",
    "logradouro": "Praca da Se",
    "complemento": "lado impar",
    "bairro": "Se",
    "localidade": "Sao Paulo",
    "uf": "SP",
    "ibge": "3550308",
}


def fake_get(payload: dict | None = None, status_code: int = 200):
    """Constroi um substituto de httpx.AsyncClient.get que devolve a resposta dada."""

    async def _get(self, url: str, *args, **kwargs) -> httpx.Response:
        return httpx.Response(
            status_code=status_code, json=payload, request=httpx.Request("GET", url)
        )

    return _get


def fake_get_timeout():
    """Substituto de httpx.AsyncClient.get que estoura o tempo limite."""

    async def _get(self, url: str, *args, **kwargs) -> httpx.Response:
        raise httpx.TimeoutException("tempo esgotado", request=httpx.Request("GET", url))

    return _get


def test_cep_traduz_a_resposta_do_viacep(client, monkeypatch):
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get(VIACEP_SUCESSO))

    response = client.get("/api/cep/01001000")

    assert response.status_code == 200
    assert response.json() == {
        "cep": "01001000",
        "street": "Praca da Se",
        "district": "Se",
        "city": "Sao Paulo",
        "state": "SP",
    }


def test_cep_inexistente_vira_404(client, monkeypatch):
    # O ViaCEP responde 200 com {"erro": true} quando o CEP nao existe.
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get({"erro": True}))

    response = client.get("/api/cep/99999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "CEP nao encontrado"}


def test_timeout_do_viacep_vira_504(client, monkeypatch):
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get_timeout())

    response = client.get("/api/cep/01001000")

    assert response.status_code == 504
    assert response.json() == {"detail": "Servico de CEP nao respondeu a tempo"}


def test_falha_do_viacep_vira_502(client, monkeypatch):
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get({}, status_code=500))

    response = client.get("/api/cep/01001000")

    assert response.status_code == 502
    assert response.json() == {"detail": "Servico de CEP indisponivel"}


@pytest.mark.parametrize("cep", ["1234567", "123456789", "abcdefgh", "01001-000"])
def test_cep_malformado_nao_chega_ao_viacep(client, monkeypatch, cep):
    def nao_deve_ser_chamado(*args, **kwargs):
        raise AssertionError("o ViaCEP nao deveria ser consultado com CEP malformado")

    monkeypatch.setattr(httpx.AsyncClient, "get", nao_deve_ser_chamado)

    assert client.get(f"/api/cep/{cep}").status_code == 422
