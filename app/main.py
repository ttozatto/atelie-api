"""Ponto de entrada da atelie-api."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import health

TAGS_METADATA = [
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

app.include_router(health.router)
