"""Gravacao, leitura e remocao das imagens no armazenamento de objetos.

As imagens ficam num servico compativel com a API do Amazon S3 (no compose, o RustFS),
acessado com o boto3. O mesmo codigo funcionaria contra o S3 da AWS trocando apenas as
variaveis de ambiente.

As obras guardam no banco so o caminho publico (`/media/<chave>.jpg`); quem serve os
bytes e a rota `GET /media/{file_name}`, que le o objeto daqui.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import PurePosixPath
from tempfile import SpooledTemporaryFile
from typing import IO
from uuid import uuid4

import boto3
from botocore.client import BaseClient, Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings

#: Tipos aceitos no upload e a extensao usada ao gravar.
ALLOWED_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

#: Tipo devolvido ao servir cada extensao.
CONTENT_TYPE_BY_EXTENSION = {
    extension: content_type for content_type, extension in ALLOWED_CONTENT_TYPES.items()
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
CHUNK_SIZE = 64 * 1024
#: Acima disso o upload passa a usar disco em vez de memoria.
SPOOL_MAX_BYTES = 1024 * 1024

#: Prefixo pelo qual as imagens sao servidas pela API.
MEDIA_URL_PREFIX = "/media"

STORAGE_UNAVAILABLE_DETAIL = "Armazenamento de imagens indisponível"


@lru_cache
def get_s3_client() -> BaseClient:
    """Cliente S3 compartilhado, apontado para o endpoint configurado."""
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        # path-style: o endpoint local nao resolve nomes do tipo <bucket>.host.
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def ensure_bucket() -> None:
    """Cria o bucket se ele ainda nao existir (chamado no startup e pelos testes)."""
    client = get_s3_client()
    bucket = get_settings().s3_bucket
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)


def _object_key(image_path: str) -> str:
    """Extrai a chave do objeto de um image_path (`/media/a1b2.jpg` -> `a1b2.jpg`)."""
    return PurePosixPath(image_path).name


async def save_image(upload: UploadFile) -> str:
    """Grava a imagem enviada no armazenamento e devolve o image_path publico.

    Recusa tipo nao suportado com 415 e arquivo acima de 10 MB com 413.
    """
    extension = ALLOWED_CONTENT_TYPES.get(upload.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato não suportado: envie jpg, jpeg, png ou webp",
        )

    key = f"{uuid4().hex}{extension}"
    with SpooledTemporaryFile(max_size=SPOOL_MAX_BYTES) as buffer:
        written = 0
        while chunk := await upload.read(CHUNK_SIZE):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Imagem acima do limite de 10 MB",
                )
            buffer.write(chunk)
        buffer.seek(0)
        put_object(key, buffer, upload.content_type or "application/octet-stream")

    return f"{MEDIA_URL_PREFIX}/{key}"


def put_object(key: str, body: IO[bytes], content_type: str) -> None:
    """Sobe um objeto para o bucket."""
    settings = get_settings()
    try:
        get_s3_client().upload_fileobj(
            body, settings.s3_bucket, key, ExtraArgs={"ContentType": content_type}
        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=STORAGE_UNAVAILABLE_DETAIL,
        ) from exc


def delete_image(image_path: str) -> None:
    """Apaga o objeto de um image_path. Chave inexistente nao e erro."""
    key = _object_key(image_path)
    if not key:
        return
    try:
        get_s3_client().delete_object(Bucket=get_settings().s3_bucket, Key=key)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=STORAGE_UNAVAILABLE_DETAIL,
        ) from exc


@dataclass
class StoredImage:
    """Objeto lido do armazenamento, pronto para ser transmitido."""

    body: IO[bytes]
    content_type: str
    content_length: int


def open_image(key: str) -> StoredImage:
    """Abre um objeto para leitura; 404 se a chave nao existir."""
    try:
        obj = get_s3_client().get_object(Bucket=get_settings().s3_bucket, Key=key)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"NoSuchKey", "404", "NoSuchBucket"}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada"
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=STORAGE_UNAVAILABLE_DETAIL,
        ) from exc
    except BotoCoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=STORAGE_UNAVAILABLE_DETAIL,
        ) from exc

    extension = PurePosixPath(key).suffix.lower()
    return StoredImage(
        body=obj["Body"],
        content_type=obj.get("ContentType")
        or CONTENT_TYPE_BY_EXTENSION.get(extension, "application/octet-stream"),
        content_length=obj.get("ContentLength", 0),
    )


def image_exists(image_path: str) -> bool:
    """Diz se o objeto de um image_path existe (usado pelos testes e pelo seed)."""
    try:
        get_s3_client().head_object(Bucket=get_settings().s3_bucket, Key=_object_key(image_path))
    except ClientError:
        return False
    return True
