"""Gravacao e remocao das imagens enviadas pelo painel."""

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings

#: Tipos aceitos no upload e a extensao usada ao gravar.
ALLOWED_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
CHUNK_SIZE = 64 * 1024

#: Prefixo sob o qual o StaticFiles serve o diretorio de media.
MEDIA_URL_PREFIX = "/media"


def media_dir() -> Path:
    """Diretorio onde as imagens ficam gravadas, criado se necessario."""
    directory = Path(get_settings().media_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


async def save_image(upload: UploadFile) -> str:
    """Grava a imagem enviada e devolve o image_path publico (ex.: /media/a1b2.jpg).

    Recusa tipo nao suportado com 415 e arquivo acima de 10 MB com 413.
    """
    extension = ALLOWED_CONTENT_TYPES.get(upload.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato não suportado: envie jpg, jpeg, png ou webp",
        )

    destination = media_dir() / f"{uuid4().hex}{extension}"
    written = 0
    try:
        with destination.open("wb") as file:
            while chunk := await upload.read(CHUNK_SIZE):
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Imagem acima do limite de 10 MB",
                    )
                file.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    return f"{MEDIA_URL_PREFIX}/{destination.name}"


def delete_image(image_path: str) -> None:
    """Apaga o arquivo de um image_path, se ele existir.

    Usa apenas o nome do arquivo, para que um caminho vindo do banco nunca escape
    do diretorio de media.
    """
    file_name = Path(image_path).name
    if file_name:
        (media_dir() / file_name).unlink(missing_ok=True)
