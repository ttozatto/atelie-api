"""Rotas do recurso photos."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select

from app.database import DbSession
from app.models.photo import Photo
from app.schemas.common import MessageResponse, Page
from app.schemas.photo import PhotoCategory, PhotoMedium, PhotoRead
from app.security import AdminGuard
from app.services.media import delete_image, save_image

router = APIRouter(prefix="/api/photos", tags=["photos"])

SIZES_DESCRIPTION = "Formatos separados por virgula, ex.: A4, A3, 30x40"


def _parse_sizes(raw_sizes: str) -> list[str]:
    """Converte "A4, A3" na lista ["A4", "A3"]."""
    return [size.strip() for size in raw_sizes.split(",") if size.strip()]


def _get_photo_or_404(db: DbSession, photo_id: int) -> Photo:
    """Busca a obra pelo id ou levanta 404."""
    photo = db.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra nao encontrada")
    return photo


@router.get(
    "",
    summary="Lista as obras com busca, filtros e paginacao",
    response_model=Page[PhotoRead],
)
def list_photos(
    db: DbSession,
    q: Annotated[str | None, Query(description="Busca no titulo e na descricao")] = None,
    category: Annotated[PhotoCategory | None, Query(description="Filtra por categoria")] = None,
    is_published: Annotated[
        bool | None, Query(description="Filtra por publicadas ou nao publicadas")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Tamanho da pagina")] = 24,
    offset: Annotated[int, Query(ge=0, description="Deslocamento")] = 0,
) -> Page[PhotoRead]:
    """Devolve a pagina de obras que atende aos filtros, da mais recente para a mais antiga."""
    filters = []
    if q:
        pattern = f"%{q}%"
        filters.append(or_(Photo.title.ilike(pattern), Photo.description.ilike(pattern)))
    if category is not None:
        filters.append(Photo.category == category.value)
    if is_published is not None:
        filters.append(Photo.is_published.is_(is_published))

    total = db.execute(select(func.count()).select_from(Photo).where(*filters)).scalar_one()
    photos = (
        db.execute(
            select(Photo)
            .where(*filters)
            .order_by(Photo.created_at.desc(), Photo.id.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return Page[PhotoRead](
        items=[PhotoRead.model_validate(photo) for photo in photos],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{photo_id}", summary="Detalha uma obra", response_model=PhotoRead)
def read_photo(db: DbSession, photo_id: int) -> PhotoRead:
    """Devolve uma obra pelo id."""
    return PhotoRead.model_validate(_get_photo_or_404(db, photo_id))


@router.post(
    "",
    summary="Cadastra uma obra com upload da imagem",
    response_model=PhotoRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_photo(
    db: DbSession,
    _: AdminGuard,
    image: Annotated[UploadFile, File(description="Imagem jpg, jpeg, png ou webp, ate 10 MB")],
    title: Annotated[str, Form(min_length=1, description="Titulo da obra")],
    medium: Annotated[PhotoMedium, Form(description="Suporte: print ou quadro")],
    price_cents: Annotated[int, Form(ge=0, description="Preco em centavos")],
    description: Annotated[str | None, Form(description="Texto livre sobre a obra")] = None,
    category: Annotated[PhotoCategory | None, Form(description="Categoria da obra")] = None,
    sizes: Annotated[str, Form(description=SIZES_DESCRIPTION)] = "",
    is_published: Annotated[bool, Form(description="Se aparece na galeria publica")] = True,
) -> PhotoRead:
    """Grava a imagem no volume de media e cria o registro da obra."""
    image_path = await save_image(image)
    photo = Photo(
        title=title,
        description=description,
        category=category.value if category else None,
        medium=medium.value,
        sizes=_parse_sizes(sizes),
        price_cents=price_cents,
        image_path=image_path,
        is_published=is_published,
    )
    db.add(photo)
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_image(image_path)
        raise
    db.refresh(photo)
    return PhotoRead.model_validate(photo)


@router.put(
    "/{photo_id}",
    summary="Atualiza os metadados de uma obra e, se enviada, a imagem",
    response_model=PhotoRead,
)
async def update_photo(
    db: DbSession,
    _: AdminGuard,
    photo_id: int,
    title: Annotated[str, Form(min_length=1, description="Titulo da obra")],
    medium: Annotated[PhotoMedium, Form(description="Suporte: print ou quadro")],
    price_cents: Annotated[int, Form(ge=0, description="Preco em centavos")],
    description: Annotated[str | None, Form(description="Texto livre sobre a obra")] = None,
    category: Annotated[PhotoCategory | None, Form(description="Categoria da obra")] = None,
    sizes: Annotated[str, Form(description=SIZES_DESCRIPTION)] = "",
    is_published: Annotated[bool, Form(description="Se aparece na galeria publica")] = True,
    image: Annotated[
        UploadFile | None, File(description="Imagem nova (opcional); mantem a atual se vazio")
    ] = None,
) -> PhotoRead:
    """Substitui os metadados da obra; troca a imagem e apaga a antiga apenas se vier uma nova."""
    photo = _get_photo_or_404(db, photo_id)
    previous_image_path: str | None = None

    if image is not None and image.filename:
        previous_image_path = photo.image_path
        photo.image_path = await save_image(image)

    photo.title = title
    photo.description = description
    photo.category = category.value if category else None
    photo.medium = medium.value
    photo.sizes = _parse_sizes(sizes)
    photo.price_cents = price_cents
    photo.is_published = is_published

    try:
        db.commit()
    except Exception:
        db.rollback()
        if previous_image_path is not None:
            delete_image(photo.image_path)
        raise

    if previous_image_path is not None:
        delete_image(previous_image_path)

    db.refresh(photo)
    return PhotoRead.model_validate(photo)


@router.delete(
    "/{photo_id}",
    summary="Exclui uma obra e o arquivo da imagem",
    response_model=MessageResponse,
)
def delete_photo(db: DbSession, _: AdminGuard, photo_id: int) -> MessageResponse:
    """Apaga o registro e, em seguida, o arquivo da imagem no volume de media."""
    photo = _get_photo_or_404(db, photo_id)
    image_path = photo.image_path
    db.delete(photo)
    db.commit()
    delete_image(image_path)
    return MessageResponse(detail="Obra excluida")
