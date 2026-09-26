"""Rota que serve as imagens guardadas no armazenamento de objetos."""

from typing import Annotated

from fastapi import APIRouter, Path
from fastapi.responses import StreamingResponse

from app.schemas.common import error_responses
from app.services.media import MEDIA_URL_PREFIX, open_image

router = APIRouter(prefix=MEDIA_URL_PREFIX, tags=["media"])

#: As imagens sao imutaveis: o nome do arquivo muda a cada upload.
CACHE_CONTROL = "public, max-age=31536000, immutable"


@router.get(
    "/{file_name}",
    summary="Serve a imagem de uma obra",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Bytes da imagem",
            "content": {"image/jpeg": {}, "image/png": {}, "image/webp": {}},
        },
        **error_responses(404, 503),
    },
)
def read_media(
    file_name: Annotated[
        str,
        Path(
            pattern=r"^[A-Za-z0-9_-]+\.(jpg|jpeg|png|webp)$",
            description="Nome do arquivo, como vem no image_path da obra",
            examples=["a1b2c3d4.jpg"],
        ),
    ],
) -> StreamingResponse:
    """Lê o objeto no armazenamento e transmite os bytes para o cliente."""
    image = open_image(file_name)
    return StreamingResponse(
        image.body,
        media_type=image.content_type,
        headers={"Cache-Control": CACHE_CONTROL, "Content-Length": str(image.content_length)},
    )
