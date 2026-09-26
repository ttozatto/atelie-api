"""Ponto de entrada da atelie-api."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.models import Customer, Photo  # noqa: F401  (o create_all precisa conhecer as tabelas)
from app.routers import auth, cep, customers, health, media, photos
from app.services.media import ensure_bucket

TAGS_METADATA = [
    {"name": "photos", "description": "Catálogo de obras: consulta pública e escrita pelo painel."},
    {"name": "customers", "description": "Cadastro de clientes interessados."},
    {
        "name": "auth",
        "description": (
            "Login do painel. Placeholder de MVP acadêmico: usuário único vindo de "
            "variável de ambiente, sem sessão e sem expiração."
        ),
    },
    {
        "name": "cep",
        "description": (
            "Proxy tratado do ViaCEP: a API consulta o serviço externo e devolve o "
            "endereço no nosso formato."
        ),
    },
    {
        "name": "media",
        "description": ("Imagens das obras, lidas do armazenamento de objetos compatível com S3."),
    },
    {"name": "health", "description": "Verificação de saúde da API e do banco."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria as tabelas e o bucket de imagens no startup (MVP academico, sem Alembic)."""
    Base.metadata.create_all(bind=engine)
    ensure_bucket()
    yield


app = FastAPI(
    title="atelie-api",
    description="API REST do catálogo de fotografias em print e quadro.",
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

app.include_router(photos.router)
app.include_router(customers.router)
app.include_router(cep.router)
app.include_router(auth.router)
app.include_router(media.router)
app.include_router(health.router)
