"""Testes do CRUD de fotos."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.services.media import media_dir


def create_photo(
    client: TestClient,
    admin_headers: dict[str, str],
    png_bytes: bytes,
    **overrides: str,
) -> dict:
    """Cadastra uma obra e devolve o corpo da resposta."""
    data = {
        "title": "Manha na Serra",
        "description": "Neblina subindo o vale.",
        "category": "paisagem",
        "medium": "print",
        "sizes": "A4, A3, 30x40",
        "price_cents": "18000",
        "is_published": "true",
    }
    data.update(overrides)
    response = client.post(
        "/api/photos",
        data=data,
        files={"image": ("obra.png", png_bytes, "image/png")},
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def stored_file(image_path: str) -> Path:
    """Caminho no disco do arquivo referenciado por um image_path."""
    return media_dir() / Path(image_path).name


def test_create_photo_grava_registro_e_arquivo(client, admin_headers, png_bytes):
    photo = create_photo(client, admin_headers, png_bytes)

    assert photo["title"] == "Manha na Serra"
    assert photo["sizes"] == ["A4", "A3", "30x40"]
    assert photo["price_cents"] == 18000
    assert photo["image_path"].startswith("/media/")
    assert stored_file(photo["image_path"]).exists()


def test_create_photo_sem_token_recusa(client, png_bytes):
    response = client.post(
        "/api/photos",
        data={"title": "Sem token", "medium": "print", "price_cents": "1000"},
        files={"image": ("obra.png", png_bytes, "image/png")},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Token do painel inválido ou ausente"}


def test_create_photo_recusa_formato_nao_suportado(client, admin_headers):
    response = client.post(
        "/api/photos",
        data={"title": "Arquivo errado", "medium": "print", "price_cents": "1000"},
        files={"image": ("obra.gif", b"nao-e-imagem-aceita", "image/gif")},
        headers=admin_headers,
    )

    assert response.status_code == 415


def test_list_photos_aplica_busca_categoria_e_publicacao(client, admin_headers, png_bytes):
    create_photo(client, admin_headers, png_bytes, title="Manha na Serra", category="paisagem")
    create_photo(client, admin_headers, png_bytes, title="Viaduto as Seis", category="urbano")
    create_photo(
        client,
        admin_headers,
        png_bytes,
        title="Ensaio sem Título",
        category="autoral",
        is_published="false",
    )

    todas = client.get("/api/photos").json()
    assert todas["total"] == 3
    assert len(todas["items"]) == 3

    busca = client.get("/api/photos", params={"q": "viaduto"}).json()
    assert [item["title"] for item in busca["items"]] == ["Viaduto as Seis"]

    por_categoria = client.get("/api/photos", params={"category": "paisagem"}).json()
    assert [item["title"] for item in por_categoria["items"]] == ["Manha na Serra"]

    publicadas = client.get("/api/photos", params={"is_published": "true"}).json()
    assert publicadas["total"] == 2

    pagina = client.get("/api/photos", params={"limit": 2, "offset": 2}).json()
    assert pagina["total"] == 3
    assert len(pagina["items"]) == 1


def test_read_photo_inexistente_retorna_404(client):
    response = client.get("/api/photos/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Obra não encontrada"}


def test_update_photo_altera_metadados_e_mantem_imagem(client, admin_headers, png_bytes):
    photo = create_photo(client, admin_headers, png_bytes)

    response = client.put(
        f"/api/photos/{photo['id']}",
        data={
            "title": "Manha na Serra (revisado)",
            "medium": "quadro",
            "price_cents": "42000",
            "sizes": "40x50",
            "is_published": "false",
        },
        headers=admin_headers,
    )

    assert response.status_code == 200
    atualizada = response.json()
    assert atualizada["title"] == "Manha na Serra (revisado)"
    assert atualizada["medium"] == "quadro"
    assert atualizada["price_cents"] == 42000
    assert atualizada["sizes"] == ["40x50"]
    assert atualizada["is_published"] is False
    assert atualizada["image_path"] == photo["image_path"]
    assert stored_file(photo["image_path"]).exists()


def test_update_photo_troca_imagem_e_apaga_a_antiga(client, admin_headers, png_bytes):
    photo = create_photo(client, admin_headers, png_bytes)

    response = client.put(
        f"/api/photos/{photo['id']}",
        data={"title": "Manha na Serra", "medium": "print", "price_cents": "18000"},
        files={"image": ("nova.png", png_bytes, "image/png")},
        headers=admin_headers,
    )

    assert response.status_code == 200
    nova = response.json()
    assert nova["image_path"] != photo["image_path"]
    assert stored_file(nova["image_path"]).exists()
    assert not stored_file(photo["image_path"]).exists()


def test_delete_photo_remove_registro_e_arquivo(client, admin_headers, png_bytes):
    photo = create_photo(client, admin_headers, png_bytes)

    response = client.delete(f"/api/photos/{photo['id']}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == {"detail": "Obra excluída"}
    assert client.get(f"/api/photos/{photo['id']}").status_code == 404
    assert not stored_file(photo["image_path"]).exists()
