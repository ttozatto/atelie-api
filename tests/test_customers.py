"""Testes do cadastro de clientes."""

CLIENTE = {
    "full_name": "Marina Duarte",
    "email": "marina@example.com",
    "phone": "11988887777",
    "cep": "01001000",
    "street": "Praca da Se",
    "number": "100",
    "complement": "apto 42",
    "district": "Se",
    "city": "Sao Paulo",
    "state": "sp",
}


def test_create_customer_grava_o_endereco_inline(client):
    response = client.post("/api/customers", json=CLIENTE)

    assert response.status_code == 201, response.text
    cliente = response.json()
    assert cliente["full_name"] == "Marina Duarte"
    assert cliente["city"] == "Sao Paulo"
    assert cliente["state"] == "SP"  # normalizado para maiusculas
    assert cliente["id"] > 0


def test_email_duplicado_retorna_409(client):
    assert client.post("/api/customers", json=CLIENTE).status_code == 201

    repetido = client.post("/api/customers", json={**CLIENTE, "full_name": "Outra Pessoa"})

    assert repetido.status_code == 409
    assert repetido.json() == {"detail": "Ja existe um cliente com este e-mail"}


def test_dados_invalidos_retornam_422(client):
    invalido = {**CLIENTE, "email": "nao-e-email", "cep": "123"}

    assert client.post("/api/customers", json=invalido).status_code == 422


def test_list_customers_pagina_do_mais_recente_para_o_mais_antigo(client):
    for indice in range(3):
        payload = {**CLIENTE, "email": f"cliente{indice}@example.com"}
        assert client.post("/api/customers", json=payload).status_code == 201

    pagina = client.get("/api/customers", params={"limit": 2}).json()

    assert pagina["total"] == 3
    assert pagina["limit"] == 2
    assert [item["email"] for item in pagina["items"]] == [
        "cliente2@example.com",
        "cliente1@example.com",
    ]
