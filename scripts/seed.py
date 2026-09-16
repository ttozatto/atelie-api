"""Popula o catalogo com 8 obras de exemplo.

As imagens sao geradas com Pillow (retangulo colorido com o titulo escrito), para a
demonstracao nao depender de subir foto real.

Uso:
    docker compose exec api python -m scripts.seed
"""

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import func, select

from app.database import Base, SessionLocal, engine
from app.models.photo import Photo
from app.services.media import MEDIA_URL_PREFIX, media_dir


@dataclass(frozen=True)
class SeedPhoto:
    """Uma obra de exemplo e a cor do retangulo gerado."""

    title: str
    description: str
    category: str
    medium: str
    sizes: list[str]
    price_cents: int
    is_published: bool
    color: tuple[int, int, int]
    size_px: tuple[int, int]


SEED_PHOTOS: list[SeedPhoto] = [
    SeedPhoto(
        title="Manha na Serra",
        description="Neblina subindo o vale nos primeiros minutos de luz.",
        category="paisagem",
        medium="print",
        sizes=["A4", "A3", "30x40"],
        price_cents=18000,
        is_published=True,
        color=(122, 141, 132),
        size_px=(1600, 1100),
    ),
    SeedPhoto(
        title="Retrato em Janela",
        description="Luz lateral de fim de tarde, filme empurrado um ponto.",
        category="retrato",
        medium="quadro",
        sizes=["30x40", "40x50"],
        price_cents=42000,
        is_published=True,
        color=(176, 142, 120),
        size_px=(1100, 1500),
    ),
    SeedPhoto(
        title="Viaduto as Seis",
        description="Rastro dos carros no horario de pico do centro.",
        category="urbano",
        medium="print",
        sizes=["A3", "50x70"],
        price_cents=22000,
        is_published=True,
        color=(96, 106, 128),
        size_px=(1600, 1100),
    ),
    SeedPhoto(
        title="Estudo de Maos",
        description="Ensaio autoral sobre gesto e repeticao.",
        category="autoral",
        medium="print",
        sizes=["A4", "A3"],
        price_cents=16000,
        is_published=True,
        color=(150, 128, 150),
        size_px=(1200, 1200),
    ),
    SeedPhoto(
        title="Dunas ao Sul",
        description="Areia varrida pelo vento, quase sem horizonte.",
        category="paisagem",
        medium="quadro",
        sizes=["40x50", "50x70"],
        price_cents=48000,
        is_published=True,
        color=(198, 170, 126),
        size_px=(1600, 1000),
    ),
    SeedPhoto(
        title="Ana, Tres Quartos",
        description="Retrato de estudio com fundo de papel cinza.",
        category="retrato",
        medium="print",
        sizes=["A4", "30x40"],
        price_cents=19000,
        is_published=True,
        color=(140, 132, 138),
        size_px=(1100, 1500),
    ),
    SeedPhoto(
        title="Escada de Servico",
        description="Geometria de concreto encontrada num predio dos anos 60.",
        category="urbano",
        medium="print",
        sizes=["A3"],
        price_cents=21000,
        is_published=True,
        color=(112, 118, 116),
        size_px=(1200, 1500),
    ),
    SeedPhoto(
        title="Ensaio sem Titulo",
        description="Serie autoral ainda em edicao, fora da galeria publica.",
        category="autoral",
        medium="quadro",
        sizes=["30x40"],
        price_cents=39000,
        is_published=False,
        color=(126, 116, 106),
        size_px=(1400, 1000),
    ),
]


def _draw_image(seed_photo: SeedPhoto, destination: Path) -> None:
    """Gera um retangulo colorido com o titulo escrito e grava em destination."""
    image = Image.new("RGB", seed_photo.size_px, seed_photo.color)
    draw = ImageDraw.Draw(image)

    # Moldura interna clara, so para a imagem de exemplo nao ficar chapada.
    margin = 48
    draw.rectangle(
        [margin, margin, seed_photo.size_px[0] - margin, seed_photo.size_px[1] - margin],
        outline=(250, 249, 247),
        width=4,
    )

    font = ImageFont.load_default(size=72)
    text_box = draw.textbbox((0, 0), seed_photo.title, font=font)
    position = (
        (seed_photo.size_px[0] - (text_box[2] - text_box[0])) // 2,
        (seed_photo.size_px[1] - (text_box[3] - text_box[1])) // 2,
    )
    draw.text(position, seed_photo.title, font=font, fill=(250, 249, 247))

    image.save(destination, format="JPEG", quality=88)


def main() -> None:
    """Cria as tabelas, checa se o catalogo esta vazio e insere as obras de exemplo."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing = db.execute(select(func.count()).select_from(Photo)).scalar_one()
        if existing:
            print(f"Catalogo ja tem {existing} obra(s); nada a fazer.")
            return

        directory = media_dir()
        for seed_photo in SEED_PHOTOS:
            file_name = f"{uuid4().hex}.jpg"
            _draw_image(seed_photo, directory / file_name)
            db.add(
                Photo(
                    title=seed_photo.title,
                    description=seed_photo.description,
                    category=seed_photo.category,
                    medium=seed_photo.medium,
                    sizes=seed_photo.sizes,
                    price_cents=seed_photo.price_cents,
                    image_path=f"{MEDIA_URL_PREFIX}/{file_name}",
                    is_published=seed_photo.is_published,
                )
            )
        db.commit()

    print(f"{len(SEED_PHOTOS)} obras de exemplo inseridas.")


if __name__ == "__main__":
    main()
