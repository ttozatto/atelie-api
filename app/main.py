"""Ponto de entrada da atelie-api."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.models import Customer, Photo  # noqa: F401  (o create_all precisa conhecer as tabelas)
from app.routers import cep, customers, health, photos
from app.services.media import MEDIA_URL_PREFIX, media_dir

TAGS_METADATA = [
    {"name": "photos", "description": "Catalogo de obras: consulta publica e escrita pelo painel."},
    {"name": "customers", "description": "Cadastro de clientes interessados."},
    {
        "name": "cep",
        "description": (
            "Proxy tratado do ViaCEP: a API consulta o servico externo e devolve o "
            "endereco no nosso formato."
        ),
    },
    {"name": "health", "description": "Verificacao de saude da API e do banco."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria as tabelas no startup (MVP academico, sem Alembic)."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="atelie-api",
    description="API REST do catalogo de fotografias em print e quadro.",
    version="0.1.0",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Imagens enviadas pelo painel, servidas direto do volume de media.
app.mount(MEDIA_URL_PREFIX, StaticFiles(directory=media_dir()), name="media")

app.include_router(photos.router)
app.include_router(customers.router)
app.include_router(cep.router)
app.include_router(health.router)
