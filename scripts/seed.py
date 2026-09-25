"""Popula o catalogo com obras de exemplo e alguns clientes interessados.

As imagens ficam versionadas em `scripts/seed_images/` — fotos do Unsplash obtidas via
Lorem Picsum, sob a Unsplash License (ver `scripts/seed_images/CREDITS.md`). Assim a
demonstracao nao depende de subir foto real nem de acesso a rede. Se algum arquivo
faltar, o script gera um retangulo colorido com Pillow no lugar.

Os enderecos dos clientes sao reais, conferidos no ViaCEP.

Uso:
    docker compose exec api python -m scripts.seed
"""

import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import func, select

from app.database import Base, SessionLocal, engine
from app.models.customer import Customer
from app.models.photo import Photo
from app.services.media import MEDIA_URL_PREFIX, media_dir

SEED_IMAGES_DIR = Path(__file__).parent / "seed_images"

#: Cor do retangulo gerado quando a imagem de exemplo nao esta disponivel.
FALLBACK_COLORS = {
    "paisagem": (122, 141, 132),
    "retrato": (176, 142, 120),
    "urbano": (96, 106, 128),
    "autoral": (150, 128, 150),
}


@dataclass(frozen=True)
class SeedPhoto:
    """Uma obra de exemplo e o arquivo de imagem correspondente."""

    image_file: str
    title: str
    description: str
    category: str
    medium: str
    sizes: list[str]
    price_cents: int
    is_published: bool = True


@dataclass(frozen=True)
class SeedCustomer:
    """Um cliente interessado de exemplo, com endereco real."""

    full_name: str
    email: str
    phone: str
    cep: str
    street: str
    number: str
    city: str
    state: str
    district: str | None = None
    complement: str | None = None


SEED_PHOTOS: list[SeedPhoto] = [
    # --- retrato ---
    SeedPhoto(
        image_file="verao-contraluz.jpg",
        title="Verão, Contraluz",
        description="Fim de tarde num campo aberto, com o sol recortando o contorno do rosto.",
        category="retrato",
        medium="print",
        sizes=["A4", "A3"],
        price_cents=19000,
    ),
    SeedPhoto(
        image_file="luz-das-seis.jpg",
        title="Luz das Seis",
        description="A última hora de luz atravessando os cabelos, sem flash e sem rebatedor.",
        category="retrato",
        medium="quadro",
        sizes=["30x40", "40x50"],
        price_cents=46000,
    ),
    SeedPhoto(
        image_file="quem-fotografa.jpg",
        title="Quem Fotografa",
        description="Retrato em preto e branco de quem está do outro lado da câmera.",
        category="retrato",
        medium="print",
        sizes=["A4", "A3", "30x40"],
        price_cents=22000,
    ),
    SeedPhoto(
        image_file="dois-de-costas.jpg",
        title="Dois, de Costas",
        description="Um banco virado para a baía e a conversa que não aparece na foto.",
        category="retrato",
        medium="print",
        sizes=["A3", "50x70"],
        price_cents=26000,
    ),
    # --- paisagem ---
    SeedPhoto(
        image_file="lago-espelho.jpg",
        title="Lago Espelho",
        description="A montanha inteira devolvida pela água parada no começo da manhã.",
        category="paisagem",
        medium="quadro",
        sizes=["40x50", "50x70"],
        price_cents=52000,
    ),
    SeedPhoto(
        image_file="rastro-na-duna.jpg",
        title="Rastro na Duna",
        description="Pegadas que o vento ainda não apagou, na crista da duna.",
        category="paisagem",
        medium="print",
        sizes=["A3", "30x40"],
        price_cents=21000,
    ),
    SeedPhoto(
        image_file="caminho-na-mata.jpg",
        title="Caminho na Mata",
        description="Trilha estreita entre troncos altos, com a neblina fechando o fundo.",
        category="paisagem",
        medium="print",
        sizes=["A4", "A3"],
        price_cents=17000,
    ),
    SeedPhoto(
        image_file="fim-de-tarde-no-campo.jpg",
        title="Fim de Tarde no Campo",
        description="O sol baixo entre as árvores, no intervalo de poucos minutos.",
        category="paisagem",
        medium="quadro",
        sizes=["30x40", "40x50"],
        price_cents=44000,
    ),
    SeedPhoto(
        image_file="travessia.jpg",
        title="Travessia",
        description="Uma pessoa sozinha no caminho, para dar escala ao vale.",
        category="paisagem",
        medium="print",
        sizes=["A3", "50x70"],
        price_cents=24000,
    ),
    SeedPhoto(
        image_file="cume-nevado.jpg",
        title="Cume Nevado",
        description="Panorâmica da serra coberta de neve, em formato bem alongado.",
        category="paisagem",
        medium="quadro",
        sizes=["50x70"],
        price_cents=68000,
    ),
    # --- urbano ---
    SeedPhoto(
        image_file="rua-das-luzes.jpg",
        title="Rua das Luzes",
        description="Varais de lâmpadas sobre a rua de pedra, já com as vitrines acesas.",
        category="urbano",
        medium="print",
        sizes=["A3", "30x40"],
        price_cents=23000,
    ),
    SeedPhoto(
        image_file="bicicleta-as-sete.jpg",
        title="Bicicleta às Sete",
        description="A fila de bicicletas antes do movimento começar no centro.",
        category="urbano",
        medium="print",
        sizes=["A4", "A3"],
        price_cents=18000,
    ),
    SeedPhoto(
        image_file="escadas-de-incendio.jpg",
        title="Escadas de Incêndio",
        description="Fachadas antigas e o desenho repetido das escadas de metal.",
        category="urbano",
        medium="quadro",
        sizes=["30x40", "40x50"],
        price_cents=43000,
    ),
    SeedPhoto(
        image_file="vertical.jpg",
        title="Vertical",
        description="A cidade vista de cima, em preto e branco, sem horizonte à vista.",
        category="urbano",
        medium="print",
        sizes=["A3", "50x70"],
        price_cents=27000,
    ),
    SeedPhoto(
        image_file="triciclo-vermelho.jpg",
        title="Triciclo Vermelho",
        description="Um triciclo esquecido na escada de entrada de um prédio de tijolos.",
        category="urbano",
        medium="print",
        sizes=["A4", "30x40"],
        price_cents=20000,
        is_published=False,
    ),
    # --- autoral ---
    SeedPhoto(
        image_file="sopro.jpg",
        title="Sopro",
        description="Um dente-de-leão inteiro na mão, um segundo antes do sopro.",
        category="autoral",
        medium="print",
        sizes=["A4", "A3"],
        price_cents=16000,
    ),
    SeedPhoto(
        image_file="gota-estudo.jpg",
        title="Gota, Estudo",
        description="Estudo de foco curto: a folha inteira fora, só a gota nítida.",
        category="autoral",
        medium="print",
        sizes=["A4"],
        price_cents=14000,
    ),
    SeedPhoto(
        image_file="outono-em-detalhe.jpg",
        title="Outono em Detalhe",
        description="Folhas secas no chão, fotografadas de muito perto.",
        category="autoral",
        medium="quadro",
        sizes=["30x40"],
        price_cents=38000,
    ),
    SeedPhoto(
        image_file="camera-antiga.jpg",
        title="A Câmera Antiga",
        description="A telemétrica de casa, parada sobre as teclas do piano.",
        category="autoral",
        medium="print",
        sizes=["A4", "A3", "30x40"],
        price_cents=25000,
    ),
    SeedPhoto(
        image_file="espiral.jpg",
        title="Espiral",
        description="Exercício de luz e giro: a lâmpada vira um ponto no fundo do túnel.",
        category="autoral",
        medium="quadro",
        sizes=["40x50"],
        price_cents=49000,
        is_published=False,
    ),
]

SEED_CUSTOMERS: list[SeedCustomer] = [
    SeedCustomer(
        full_name="Marina Duarte",
        email="marina.duarte@example.com",
        phone="11988887777",
        cep="01310100",
        street="Avenida Paulista",
        number="1578",
        complement="apto 92",
        district="Bela Vista",
        city="São Paulo",
        state="SP",
    ),
    SeedCustomer(
        full_name="Rafael Andrade",
        email="rafael.andrade@example.com",
        phone="21977776666",
        cep="22280030",
        street="Rua Dezenove de Fevereiro",
        number="120",
        district="Botafogo",
        city="Rio de Janeiro",
        state="RJ",
    ),
    SeedCustomer(
        full_name="Beatriz Nogueira",
        email="beatriz.nogueira@example.com",
        phone="31966665555",
        cep="30130010",
        street="Praça Sete de Setembro",
        number="45",
        complement="sala 3",
        district="Centro",
        city="Belo Horizonte",
        state="MG",
    ),
    SeedCustomer(
        full_name="Henrique Sato",
        email="henrique.sato@example.com",
        phone="41955554444",
        cep="80010000",
        street="Rua José Loureiro",
        number="310",
        district="Centro",
        city="Curitiba",
        state="PR",
    ),
    SeedCustomer(
        full_name="Camila Ferrão",
        email="camila.ferrao@example.com",
        phone="51944443333",
        cep="90010150",
        street="Praça da Alfândega",
        number="8",
        district="Centro Histórico",
        city="Porto Alegre",
        state="RS",
    ),
]


def _draw_placeholder(seed_photo: SeedPhoto, destination: Path) -> None:
    """Gera um retangulo colorido com o titulo, usado quando falta a imagem de exemplo."""
    width, height = 1400, 1000
    color = FALLBACK_COLORS.get(seed_photo.category, (130, 130, 130))
    image = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(image)
    draw.rectangle([48, 48, width - 48, height - 48], outline=(250, 249, 247), width=4)

    # A fonte embutida do Pillow nao tem glifos acentuados; so o texto desenhado perde o
    # acento, o titulo gravado no banco continua acentuado.
    label = unicodedata.normalize("NFKD", seed_photo.title).encode("ascii", "ignore").decode()
    font = ImageFont.load_default(size=72)
    box = draw.textbbox((0, 0), label, font=font)
    position = ((width - (box[2] - box[0])) // 2, (height - (box[3] - box[1])) // 2)
    draw.text(position, label, font=font, fill=(250, 249, 247))

    image.save(destination, format="JPEG", quality=88)


def _put_image_in_media(seed_photo: SeedPhoto) -> str:
    """Coloca a imagem da obra no volume de media e devolve o image_path publico."""
    source = SEED_IMAGES_DIR / seed_photo.image_file
    file_name = f"{uuid4().hex}.jpg"
    destination = media_dir() / file_name

    if source.is_file():
        shutil.copyfile(source, destination)
    else:
        print(f"  aviso: {seed_photo.image_file} nao encontrado, gerando uma imagem no lugar")
        _draw_placeholder(seed_photo, destination)

    return f"{MEDIA_URL_PREFIX}/{file_name}"


def _seed_photos(db) -> None:
    """Insere as obras de exemplo, se o catalogo estiver vazio."""
    existing = db.execute(select(func.count()).select_from(Photo)).scalar_one()
    if existing:
        print(f"Catálogo já tem {existing} obra(s); nada a fazer.")
        return

    for seed_photo in SEED_PHOTOS:
        db.add(
            Photo(
                title=seed_photo.title,
                description=seed_photo.description,
                category=seed_photo.category,
                medium=seed_photo.medium,
                sizes=seed_photo.sizes,
                price_cents=seed_photo.price_cents,
                image_path=_put_image_in_media(seed_photo),
                is_published=seed_photo.is_published,
            )
        )
    db.commit()

    publicadas = sum(1 for p in SEED_PHOTOS if p.is_published)
    print(
        f"{len(SEED_PHOTOS)} obras inseridas ({publicadas} publicadas, "
        f"{len(SEED_PHOTOS) - publicadas} em rascunho)."
    )


def _seed_customers(db) -> None:
    """Insere os clientes de exemplo, se ainda nao houver nenhum."""
    existing = db.execute(select(func.count()).select_from(Customer)).scalar_one()
    if existing:
        print(f"Já há {existing} cliente(s) cadastrado(s); nada a fazer.")
        return

    for seed_customer in SEED_CUSTOMERS:
        db.add(Customer(**vars(seed_customer)))
    db.commit()
    print(f"{len(SEED_CUSTOMERS)} clientes inseridos.")


def main() -> None:
    """Cria as tabelas e popula obras e clientes."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        _seed_photos(db)
        _seed_customers(db)


if __name__ == "__main__":
    main()
