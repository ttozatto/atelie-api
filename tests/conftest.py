"""Fixtures dos testes.

Os testes usam um banco proprio (`<banco>_test`) e um diretorio de media temporario,
para nunca mexer nos dados de desenvolvimento. Nenhum teste acessa a rede.
"""

import os
import tempfile
from collections.abc import Generator
from io import BytesIO

# Precisa vir antes de importar a app: as configuracoes sao lidas no import.
os.environ["MEDIA_DIR"] = tempfile.mkdtemp(prefix="atelie-media-test-")
os.environ["ADMIN_TOKEN"] = "token-de-teste"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402
from sqlalchemy import Engine, create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    """Cria (se preciso) e prepara o banco de testes."""
    url = make_url(get_settings().database_url)
    test_database = f"{url.database}_test"

    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": test_database}
        ).scalar()
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{test_database}"'))
    admin_engine.dispose()

    engine = create_engine(url.set(database=test_database))
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(test_engine: Engine) -> None:
    """Esvazia as tabelas antes de cada teste."""
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with test_engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(test_engine: Engine) -> Generator[TestClient, None, None]:
    """Cliente HTTP da app, com o banco de testes injetado."""
    session_factory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    def override_get_db() -> Generator[object, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers() -> dict[str, str]:
    """Header do painel com o token esperado."""
    return {"X-Admin-Token": "token-de-teste"}


@pytest.fixture
def png_bytes() -> bytes:
    """Um PNG minimo valido, gerado em memoria."""
    buffer = BytesIO()
    Image.new("RGB", (8, 8), (120, 130, 125)).save(buffer, format="PNG")
    return buffer.getvalue()
