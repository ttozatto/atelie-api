"""Testes do login do painel."""

import pytest

CREDENCIAIS_VALIDAS = {"username": "admin-de-teste", "password": "senha-de-teste"}


def test_login_valido_devolve_o_token(client):
    response = client.post("/api/auth/login", json=CREDENCIAIS_VALIDAS)

    assert response.status_code == 200, response.text
    corpo = response.json()
    assert corpo["username"] == "admin-de-teste"
    assert corpo["token"] == "token-de-teste"


def test_token_devolvido_abre_as_rotas_de_escrita(client, png_bytes):
    token = client.post("/api/auth/login", json=CREDENCIAIS_VALIDAS).json()["token"]

    response = client.post(
        "/api/photos",
        data={"title": "Obra do login", "medium": "print", "price_cents": "1000"},
        files={"image": ("obra.png", png_bytes, "image/png")},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 201


@pytest.mark.parametrize(
    "credenciais",
    [
        {"username": "admin-de-teste", "password": "senha-errada"},
        {"username": "outro-usuario", "password": "senha-de-teste"},
        {"username": "outro-usuario", "password": "senha-errada"},
    ],
)
def test_credenciais_invalidas_retornam_401(client, credenciais):
    response = client.post("/api/auth/login", json=credenciais)

    assert response.status_code == 401
    assert response.json() == {"detail": "Usuário ou senha inválidos"}


def test_campos_faltando_retornam_422(client):
    assert client.post("/api/auth/login", json={"username": "admin-de-teste"}).status_code == 422
    assert client.post("/api/auth/login", json={}).status_code == 422
