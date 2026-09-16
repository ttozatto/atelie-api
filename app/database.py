"""Engine, sessao e Base declarativa do SQLAlchemy."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base declarativa compartilhada pelos models."""


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI que abre e fecha uma sessao por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#: Sessao do banco injetada nas rotas.
DbSession = Annotated[Session, Depends(get_db)]
